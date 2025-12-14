"""
Tool functions for DynamoDB queries
These functions are registered with Gemini API for function calling
"""
import boto3
import os
import logging
import time
from typing import Dict, List, Optional, Any
from decimal import Decimal

logger = logging.getLogger(__name__)

def convert_dynamodb_value(value):
    """Convert DynamoDB types (Decimal, etc.) to Python native types for JSON serialization"""
    if isinstance(value, Decimal):
        # Convert Decimal to int if it's a whole number, otherwise float
        if value % 1 == 0:
            return int(value)
        return float(value)
    elif isinstance(value, dict):
        return {k: convert_dynamodb_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [convert_dynamodb_value(v) for v in value]
    return value

# Lazy initialization of RAG service
_rag_service = None

def get_rag_service():
    """Get or initialize RAG service"""
    import time
    global _rag_service
    if _rag_service is None:
        try:
            logger.info("Initializing RAG service (first time)...")
            init_start = time.time()
            # Try relative import first, fallback to absolute import
            try:
                from services.rag_service import RAGService
            except ImportError:
                from app.api.v1.chat.services.rag_service import RAGService
            _rag_service = RAGService()
            _rag_service.initialize()
            init_time = time.time() - init_start
            logger.info(f"RAG service initialized in {init_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Could not initialize RAG service: {e}. Falling back to exact match.")
            import traceback
            logger.error(traceback.format_exc())
            return None
    else:
        logger.debug("RAG service already initialized, reusing")
    return _rag_service

# Frontend base URL (configure via environment variable)
FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', 'https://nihongo.cloud')

def get_word_detail_url(word_id: int) -> str:
    """Generate frontend URL for word detail page"""
    return f"{FRONTEND_BASE_URL}/words/{word_id}"

def get_kanji_detail_url(kanji_id: int) -> str:
    """Generate frontend URL for kanji detail page"""
    return f"{FRONTEND_BASE_URL}/kanjis/{kanji_id}"

def search_word_by_name(word_name: str) -> Dict[str, Any]:
    """
    Search for a word by name (Japanese or English) using vector search
    
    This function is called by Gemini when user asks about a word.
    Uses vector similarity search first, falls back to exact match if needed.
    
    Args:
        word_name: Word name to search (can be Japanese or English)
    
    Returns:
        {
            "found": bool,
            "word": {
                "id": int,
                "name": str,
                "hiragana": str,
                "english": str,
                "level": int,
                "detail_url": str  # Frontend URL
            } | None,
            "message": str
        }
    """
    try:
        # First, try vector search
        logger.info(f"Attempting vector search for word: '{word_name}'")
        search_start = time.time()
        rag_service = get_rag_service()
        if rag_service:
            try:
                logger.info("Calling rag_service.search_words...")
                vector_results = rag_service.search_words(word_name, k=3)
                search_time = time.time() - search_start
                logger.info(f"Vector search completed in {search_time:.2f} seconds, found {len(vector_results) if vector_results else 0} results")
                if vector_results:
                    # Use the best match (lowest score = most similar)
                    best_match = vector_results[0]
                    word_id = best_match.get('id')
                    if word_id is not None:
                        # Convert all values to native Python types for JSON serialization
                        level = best_match.get('level', 0)
                        level = convert_dynamodb_value(level) if level is not None else 0
                        level = int(level) if isinstance(level, (int, float)) else 0
                        
                        logger.info(f"Found word via vector search: {best_match.get('name')} (score: {best_match.get('score')})")
                        return {
                            "found": True,
                            "word": {
                                "id": int(word_id),
                                "name": str(best_match.get('name', '')),
                                "hiragana": str(best_match.get('hiragana', '')),
                                "english": str(best_match.get('english', '')),
                                "level": level,
                                "detail_url": get_word_detail_url(int(word_id))
                            },
                            "message": f"Found word via semantic search: {best_match.get('name')}"
                        }
            except Exception as e:
                logger.warning(f"Vector search failed: {e}. Falling back to exact match.")
        
        # Fallback to exact match search
        # Create DynamoDB client directly (similar to words module)
        import boto3
        table_name = os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        # Query all words (remove 1000 limit to search all words)
        all_items = []
        last_evaluated_key = None
        
        while True:
            query_params = {
                "KeyConditionExpression": "PK = :pk",
                "ExpressionAttributeValues": {
                    ":pk": "WORD"
                }
            }
            if last_evaluated_key:
                query_params["ExclusiveStartKey"] = last_evaluated_key
            
            response = table.query(**query_params)
            items = response.get('Items', [])
            all_items.extend(items)
            
            last_evaluated_key = response.get('LastEvaluatedKey')
            if not last_evaluated_key:
                break
        
        # Convert DynamoDB items to word format
        words = []
        for item in all_items:
            try:
                word_id = int(item.get('SK', '0'))
                level = item.get('level', 0)
                level = convert_dynamodb_value(level) if level is not None else 0
                level = int(level) if isinstance(level, (int, float)) else 0
                words.append({
                    'id': word_id,
                    'name': str(item.get('name', '')),
                    'hiragana': str(item.get('hiragana', '')),
                    'english': str(item.get('english', '')),
                    'level': level
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Error converting word item {item.get('SK', 'unknown')}: {e}")
                continue
        
        # Search for matching word (case-insensitive)
        word_name_lower = word_name.lower().strip()
        word_name_original = word_name.strip()
        
        logger.info(f"Searching for word: '{word_name}' (lowercase: '{word_name_lower}')")
        logger.info(f"Total words to search: {len(words)}")
        
        # First, try exact match (case-sensitive)
        for word in words:
            if word.get('name') == word_name_original:
                logger.info(f"Found exact match: {word.get('name')} (ID: {word.get('id')})")
                return {
                    "found": True,
                    "word": {
                        "id": word.get('id'),
                        "name": word.get('name'),
                        "hiragana": word.get('hiragana', ''),
                        "english": word.get('english', ''),
                        "level": word.get('level', 0),
                        "detail_url": get_word_detail_url(word.get('id'))
                    },
                    "message": f"Found word: {word.get('name')}"
                }
        
        # Then, try case-insensitive exact match
        for word in words:
            if word.get('name') and word_name_lower == word.get('name', '').lower():
                logger.info(f"Found case-insensitive exact match: {word.get('name')} (ID: {word.get('id')})")
                return {
                    "found": True,
                    "word": {
                        "id": word.get('id'),
                        "name": word.get('name'),
                        "hiragana": word.get('hiragana', ''),
                        "english": word.get('english', ''),
                        "level": word.get('level', 0),
                        "detail_url": get_word_detail_url(word.get('id'))
                    },
                    "message": f"Found word: {word.get('name')}"
                }
        
        # Finally, try partial match
        for word in words:
            # Check Japanese name (partial match)
            if word.get('name') and word_name_lower in word.get('name', '').lower():
                logger.info(f"Found partial match in name: {word.get('name')} (ID: {word.get('id')})")
                return {
                    "found": True,
                    "word": {
                        "id": word.get('id'),
                        "name": word.get('name'),
                        "hiragana": word.get('hiragana', ''),
                        "english": word.get('english', ''),
                        "level": word.get('level', 0),
                        "detail_url": get_word_detail_url(word.get('id'))
                    },
                    "message": f"Found word: {word.get('name')}"
                }
            
            # Check English translation (partial match)
            if word.get('english') and word_name_lower in word.get('english', '').lower():
                logger.info(f"Found partial match in English: {word.get('name')} ({word.get('english')}) (ID: {word.get('id')})")
                return {
                    "found": True,
                    "word": {
                        "id": word.get('id'),
                        "name": word.get('name'),
                        "hiragana": word.get('hiragana', ''),
                        "english": word.get('english', ''),
                        "level": word.get('level', 0),
                        "detail_url": get_word_detail_url(word.get('id'))
                    },
                    "message": f"Found word: {word.get('name')} ({word.get('english')})"
                }
        
        logger.warning(f"Word '{word_name}' not found in {len(words)} words")
        
        return {
            "found": False,
            "word": None,
            "message": f"Word '{word_name}' not found"
        }
    
    except Exception as e:
        logger.error(f"Error searching word '{word_name}': {str(e)}")
        return {
            "found": False,
            "word": None,
            "message": f"Error searching for word: {str(e)}"
        }

def get_word_by_id(word_id: int) -> Dict[str, Any]:
    """
    Get word details by ID
    
    Args:
        word_id: Word ID
    
    Returns:
        {
            "found": bool,
            "word": {
                "id": int,
                "name": str,
                "hiragana": str,
                "english": str,
                "level": int,
                "detail_url": str
            } | None,
            "message": str
        }
    """
    try:
        # Create DynamoDB client directly
        import boto3
        table_name = os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        # Get word by ID
        response = table.get_item(
            Key={
                'PK': "WORD",
                'SK': str(word_id)
            }
        )
        
        item = response.get('Item')
        if item:
            level = item.get('level', 0)
            level = convert_dynamodb_value(level) if level is not None else 0
            level = int(level) if isinstance(level, (int, float)) else 0
            word = {
                'id': word_id,
                'name': str(item.get('name', '')),
                'hiragana': str(item.get('hiragana', '')),
                'english': str(item.get('english', '')),
                'level': level
            }
            return {
                "found": True,
                "word": {
                    "id": word['id'],
                    "name": word['name'],
                    "hiragana": word['hiragana'],
                    "english": word['english'],
                    "level": word['level'],
                    "detail_url": get_word_detail_url(word['id'])
                },
                "message": f"Found word: {word['name']}"
            }
        else:
            return {
                "found": False,
                "word": None,
                "message": f"Word with ID {word_id} not found"
            }
    
    except Exception as e:
        logger.error(f"Error getting word {word_id}: {str(e)}")
        return {
            "found": False,
            "word": None,
            "message": f"Error getting word: {str(e)}"
        }

def search_kanji_by_character(kanji_character: str) -> Dict[str, Any]:
    """
    Search for a kanji by character using vector search
    
    Args:
        kanji_character: Kanji character to search (can be character, meaning, or reading)
    
    Returns:
        {
            "found": bool,
            "kanji": {
                "id": int,
                "kanji": str,
                "meaning": str,
                "reading": str,
                "detail_url": str
            } | None,
            "message": str
        }
    """
    try:
        kanji_char = kanji_character.strip()
        
        # First, try vector search
        rag_service = get_rag_service()
        if rag_service:
            try:
                vector_results = rag_service.search_kanjis(kanji_char, k=3)
                if vector_results:
                    # Use the best match (lowest score = most similar)
                    best_match = vector_results[0]
                    kanji_id = best_match.get('id')
                    if kanji_id is not None:
                        # Try both 'kanji' and 'character' field names for compatibility
                        kanji_char = best_match.get('kanji') or best_match.get('character', '')
                        logger.info(f"Found kanji via vector search: {kanji_char} (score: {best_match.get('score')})")
                        return {
                            "found": True,
                            "kanji": {
                                "id": int(kanji_id),
                                "kanji": str(kanji_char),
                                "character": str(kanji_char),  # Also include as 'character' for compatibility
                                "meaning": str(best_match.get('meaning', '')),
                                "reading": str(best_match.get('reading', '')),
                                "detail_url": get_kanji_detail_url(int(kanji_id))
                            },
                            "message": f"Found kanji via semantic search: {kanji_char}"
                        }
            except Exception as e:
                logger.warning(f"Vector search failed: {e}. Falling back to exact match.")
        
        # Fallback to exact match search
        import boto3
        table_name = os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        # Query all kanjis
        all_items = []
        last_evaluated_key = None
        
        while True:
            query_params = {
                "KeyConditionExpression": "PK = :pk",
                "ExpressionAttributeValues": {
                    ":pk": "KANJI"
                }
            }
            if last_evaluated_key:
                query_params["ExclusiveStartKey"] = last_evaluated_key
            
            response = table.query(**query_params)
            items = response.get('Items', [])
            all_items.extend(items)
            
            last_evaluated_key = response.get('LastEvaluatedKey')
            if not last_evaluated_key:
                break
            
            # Limit to 1000 items for performance
            if len(all_items) >= 1000:
                break
        
        # Search for matching kanji
        for item in all_items[:1000]:  # Limit to 1000
            kanji_id = int(item.get('SK', '0'))
            # Try both 'kanji' and 'character' field names for compatibility
            kanji_text = item.get('kanji') or item.get('character', '')
            
            if kanji_text == kanji_char:
                return {
                    "found": True,
                    "kanji": {
                        "id": kanji_id,
                        "kanji": kanji_text,
                        "meaning": item.get('meaning', ''),
                        "reading": item.get('reading', ''),
                        "detail_url": get_kanji_detail_url(kanji_id)
                    },
                    "message": f"Found kanji: {kanji_char}"
                }
        
        return {
            "found": False,
            "kanji": None,
            "message": f"Kanji '{kanji_char}' not found"
        }
    
    except Exception as e:
        logger.error(f"Error searching kanji '{kanji_character}': {str(e)}")
        return {
            "found": False,
            "kanji": None,
            "message": f"Error searching for kanji: {str(e)}"
        }

# Tool function registry for Gemini
TOOL_FUNCTIONS = {
    "search_word_by_name": {
        "function": search_word_by_name,
        "description": "Search for a Japanese word by its name (Japanese or English) using semantic search. This can find words even if the exact spelling doesn't match. Use this when user asks 'What does XXX mean?' or 'What is XXX in Japanese?'. The result includes a 'detail_url' field that should be included in the response as a clickable link.",
        "parameters": {
            "type": "object",
            "properties": {
                "word_name": {
                    "type": "string",
                    "description": "The word name to search for (can be Japanese or English). Can be partial or similar words - semantic search will find related matches."
                }
            },
            "required": ["word_name"]
        }
    },
    "get_word_by_id": {
        "function": get_word_by_id,
        "description": "Get detailed information about a word by its ID. Use this when you have a word ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "word_id": {
                    "type": "integer",
                    "description": "The word ID"
                }
            },
            "required": ["word_id"]
        }
    },
    "search_kanji_by_character": {
        "function": search_kanji_by_character,
        "description": "Search for a kanji by its character, meaning, or reading using semantic search. This can find kanjis even if the exact character doesn't match. Use this when user asks about a specific kanji character, its meaning, or reading. The result includes a 'detail_url' field that should be included in the response as a clickable link.",
        "parameters": {
            "type": "object",
            "properties": {
                "kanji_character": {
                    "type": "string",
                    "description": "The kanji character, meaning, or reading to search for. Can be partial or similar - semantic search will find related matches."
                }
            },
            "required": ["kanji_character"]
        }
    }
}

