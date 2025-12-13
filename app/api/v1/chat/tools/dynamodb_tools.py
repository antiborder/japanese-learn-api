"""
Tool functions for DynamoDB queries
These functions are registered with Gemini API for function calling
"""
import boto3
import os
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

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
    Search for a word by name (Japanese or English)
    
    This function is called by Gemini when user asks about a word.
    
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
                words.append({
                    'id': word_id,
                    'name': item.get('name', ''),
                    'hiragana': item.get('hiragana', ''),
                    'english': item.get('english', ''),
                    'level': int(item.get('level', 0)) if item.get('level') else 0
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
            word = {
                'id': word_id,
                'name': item.get('name', ''),
                'hiragana': item.get('hiragana', ''),
                'english': item.get('english', ''),
                'level': int(item.get('level', 0)) if item.get('level') else 0
            }
        
        if item:
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
    Search for a kanji by character
    
    Args:
        kanji_character: Kanji character to search
    
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
        # Create DynamoDB client directly
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
        
        kanji_char = kanji_character.strip()
        
        # Search for matching kanji
        for item in all_items[:1000]:  # Limit to 1000
            kanji_id = int(item.get('SK', '0'))
            kanji_text = item.get('kanji', '')
            
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
        "description": "Search for a Japanese word by its name (Japanese or English). Use this when user asks 'What does XXX mean?' or 'What is XXX in Japanese?'. The result includes a 'detail_url' field that should be included in the response as a clickable link.",
        "parameters": {
            "type": "object",
            "properties": {
                "word_name": {
                    "type": "string",
                    "description": "The word name to search for (can be Japanese or English)"
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
        "description": "Search for a kanji by its character. Use this when user asks about a specific kanji character or its reading. The result includes a 'detail_url' field that should be included in the response as a clickable link.",
        "parameters": {
            "type": "object",
            "properties": {
                "kanji_character": {
                    "type": "string",
                    "description": "The kanji character to search for"
                }
            },
            "required": ["kanji_character"]
        }
    }
}

