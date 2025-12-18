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
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

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
    Uses vector similarity search with 20 second timeout.
    If the best match and 2nd place are close (within 30 points), returns up to 3 candidates
    (words and/or kanjis combined, sorted by score).
    
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
            "candidates": {
                "words": List[Dict],  # Word candidates from top 3 (if any)
                "kanjis": List[Dict],  # Kanji candidates from top 3 (if any)
                "combined": List[Dict]  # Top 3 candidates (words + kanjis combined, sorted by score)
                                       # Each candidate has "type" field ("word" or "kanji") and "id" field
            } | None,
            "message": str
        }
        
    Note: Maximum 3 candidates are returned (combined from words and kanjis, sorted by similarity score).
    """
    # Score threshold: FAISS returns L2 distance (not normalized), so scores are typically in 100-400 range
    # Use relative threshold: if the difference between 1st and 2nd place is small, return multiple candidates
    # This helps when multiple words have similar scores (e.g., "戦う" variants: 戦います, 戦争, etc.)
    # Based on actual logs, scores are typically 100-400, so we use a relative difference threshold
    SCORE_DIFF_THRESHOLD = 30.0  # If 2nd place is within 30 points of 1st place, return candidates
    
    try:
        # First, try vector search with timeout
        logger.info(f"Attempting vector search for word: '{word_name}'")
        search_start = time.time()
        rag_service = get_rag_service()
        
        if rag_service:
            try:
                # Execute vector search with 20 second timeout
                # Temporarily use k=10 to check top 10 scores for debugging
                def _vector_search():
                    return rag_service.search_words(word_name, k=10)
                
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(_vector_search)
                    try:
                        vector_results = future.result(timeout=20.0)
                        search_time = time.time() - search_start
                        logger.info(f"Vector search completed in {search_time:.2f} seconds, found {len(vector_results) if vector_results else 0} results")
                        
                        # Log top 10 results with scores for debugging
                        if vector_results:
                            logger.info(f"Top 10 vector search results for '{word_name}':")
                            for i, result in enumerate(vector_results[:10], 1):
                                word_name_result = result.get('name', 'N/A')
                                score = result.get('score', float('inf'))
                                logger.info(f"  {i}. {word_name_result} (score: {score:.4f})")
                        
                        if vector_results:
                            best_match = vector_results[0]
                            best_score = best_match.get('score', float('inf'))
                            word_id = best_match.get('id')
                            
                            # Check if we should return multiple candidates
                            # Use relative threshold: if 2nd place is close to 1st place, return candidates
                            should_return_candidates = False
                            if len(vector_results) >= 2:
                                second_score = vector_results[1].get('score', float('inf'))
                                score_diff = second_score - best_score
                                if score_diff <= SCORE_DIFF_THRESHOLD:
                                    should_return_candidates = True
                                    logger.info(f"Best match score ({best_score:.2f}) and 2nd place ({second_score:.2f}) are close (diff: {score_diff:.2f}), searching for candidates")
                            
                            if should_return_candidates:
                                
                                # Search for word and kanji candidates
                                # Temporarily use k=10 to check top 10 scores for debugging
                                def _search_all():
                                    return rag_service.search_all(word_name, k=10)
                                
                                with ThreadPoolExecutor(max_workers=1) as executor2:
                                    future2 = executor2.submit(_search_all)
                                    try:
                                        all_results = future2.result(timeout=15.0)  # 15秒のタイムアウト
                                        
                                        # Log top 10 word and kanji results for debugging
                                        word_results = all_results.get('words', [])[:10]
                                        kanji_results = all_results.get('kanjis', [])[:10]
                                        logger.info(f"Top 10 word candidates for '{word_name}':")
                                        for i, word_result in enumerate(word_results, 1):
                                            word_name_result = word_result.get('name', 'N/A')
                                            score = word_result.get('score', float('inf'))
                                            logger.info(f"  {i}. {word_name_result} (score: {score:.4f})")
                                        logger.info(f"Top 10 kanji candidates for '{word_name}':")
                                        for i, kanji_result in enumerate(kanji_results, 1):
                                            kanji_char_result = kanji_result.get('kanji') or kanji_result.get('character', 'N/A')
                                            score = kanji_result.get('score', float('inf'))
                                            logger.info(f"  {i}. {kanji_char_result} (score: {score:.4f})")
                                        
                                        # Combine words and kanjis, sort by score (lower is better), and take top 3
                                        combined_candidates = []
                                        
                                        # Format word candidates
                                        for word_result in all_results.get('words', []):
                                            word_id_candidate = word_result.get('id')
                                            if word_id_candidate is not None:
                                                level = word_result.get('level', 0)
                                                level = convert_dynamodb_value(level) if level is not None else 0
                                                level = int(level) if isinstance(level, (int, float)) else 0
                                                
                                                combined_candidates.append({
                                                    "type": "word",
                                                    "id": int(word_id_candidate),
                                                    "name": str(word_result.get('name', '')),
                                                    "hiragana": str(word_result.get('hiragana', '')),
                                                    "english": str(word_result.get('english', '')),
                                                    "level": level,
                                                    "score": float(word_result.get('score', 0)),
                                                    "detail_url": get_word_detail_url(int(word_id_candidate))
                                                })
                                        
                                        # Format kanji candidates
                                        for kanji_result in all_results.get('kanjis', []):
                                            kanji_id_candidate = kanji_result.get('id')
                                            if kanji_id_candidate is not None:
                                                kanji_char = kanji_result.get('kanji') or kanji_result.get('character', '')
                                                combined_candidates.append({
                                                    "type": "kanji",
                                                    "id": int(kanji_id_candidate),
                                                    "kanji": str(kanji_char),
                                                    "character": str(kanji_char),
                                                    "meaning": str(kanji_result.get('meaning', '')),
                                                    "reading": str(kanji_result.get('reading', '')),
                                                    "score": float(kanji_result.get('score', 0)),
                                                    "detail_url": get_kanji_detail_url(int(kanji_id_candidate))
                                                })
                                        
                                        # Sort by score (lower is better) and take top 3
                                        combined_candidates.sort(key=lambda x: x.get('score', float('inf')))
                                        top_candidates = combined_candidates[:3]
                                        
                                        # Create a deep copy of top_candidates for combined list (to preserve type field)
                                        # This ensures that when we remove 'type' from word_candidates/kanji_candidates,
                                        # the combined list still has the type field
                                        import copy
                                        combined_with_type = copy.deepcopy(top_candidates)
                                        
                                        # Separate back into words and kanjis for backward compatibility
                                        word_candidates = [c for c in top_candidates if c.get('type') == 'word']
                                        kanji_candidates = [c for c in top_candidates if c.get('type') == 'kanji']
                                        
                                        # Remove 'type' field from individual candidates (keep it in combined list for frontend)
                                        for candidate in word_candidates:
                                            candidate.pop('type', None)
                                        for candidate in kanji_candidates:
                                            candidate.pop('type', None)
                                        
                                        logger.info(f"Found {len(word_candidates)} word candidates and {len(kanji_candidates)} kanji candidates (top 3 combined)")
                                        
                                        return {
                                            "found": False,
                                            "word": None,
                                            "candidates": {
                                                "words": word_candidates,
                                                "kanjis": kanji_candidates,
                                                "combined": combined_with_type  # Combined list with type field preserved
                                            },
                                            "message": f"'{word_name}'に完全一致する単語は見つかりませんでしたが、以下の候補が見つかりました。"
                                        }
                                    except FutureTimeoutError:
                                        logger.warning("Candidate search timed out")
                                        # Fall through to return not found
                            
                            # High confidence match (score <= threshold)
                            if word_id is not None:
                                level = best_match.get('level', 0)
                                level = convert_dynamodb_value(level) if level is not None else 0
                                level = int(level) if isinstance(level, (int, float)) else 0
                                
                                logger.info(f"Found word via vector search: {best_match.get('name')} (score: {best_score})")
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
                                    "candidates": None,
                                    "message": f"Found word via semantic search: {best_match.get('name')}"
                                }
                    except FutureTimeoutError:
                        search_time = time.time() - search_start
                        logger.warning(f"Vector search timed out after {search_time:.2f} seconds for '{word_name}'")
                        return {
                            "found": False,
                            "word": None,
                            "candidates": None,
                            "message": "その言葉について特定するためにもう少し詳しく教えてください。例えば、漢字表記や英語での意味、文脈などを含めて質問していただけると、より正確にお答えできます。"
                        }
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
        
        # If vector search didn't find anything or failed, return not found
        logger.warning(f"Word '{word_name}' not found via vector search")
        return {
            "found": False,
            "word": None,
            "candidates": None,
            "message": "その言葉について特定するためにもう少し詳しく教えてください。例えば、漢字表記や英語での意味、文脈などを含めて質問していただけると、より正確にお答えできます。"
        }
    
    except Exception as e:
        logger.error(f"Error searching word '{word_name}': {str(e)}")
        return {
            "found": False,
            "word": None,
            "candidates": None,
            "message": "その言葉について特定するためにもう少し詳しく教えてください。例えば、漢字表記や英語での意味、文脈などを含めて質問していただけると、より正確にお答えできます。"
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
        "description": "Search for a Japanese word by its name (Japanese or English) using semantic search. This can find words even if the exact spelling doesn't match. Use this when user asks 'What does XXX mean?' or 'What is XXX in Japanese?'. Do NOT include detail_url links in your response - the frontend will handle displaying cards based on IDs.",
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
        "description": "Search for a kanji by its character, meaning, or reading using semantic search. This can find kanjis even if the exact character doesn't match. Use this when user asks about a specific kanji character, its meaning, or reading. Do NOT include detail_url links in your response - the frontend will handle displaying cards based on IDs.",
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

