"""
Tool functions for DynamoDB queries
These functions are registered with Gemini API for function calling
"""
import boto3
import os
import logging
import time
import threading
from typing import Dict, List, Optional, Any
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import re

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

_JP_TOKEN_RE = re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3400-\u4DBF\u3005\u30FC]+")

def _extract_target_term(text: str) -> str:
    """
    Extract the most likely target Japanese term from a full user sentence.
    We prefer content inside Japanese quotes first, otherwise the longest Japanese token.
    """
    if not text:
        return ""
    s = str(text).strip()
    # Prefer quoted segments (「...」, 『...』, "..." , '...')
    quote_patterns = [
        r"「([^」]+)」",
        r"『([^』]+)』",
        r"\"([^\"]+)\"",
        r"'([^']+)'",
    ]
    for pat in quote_patterns:
        m = re.search(pat, s)
        if m:
            candidate = m.group(1).strip()
            jp_tokens = _JP_TOKEN_RE.findall(candidate)
            if jp_tokens:
                # If quoted content includes Japanese, use the longest Japanese token within it.
                return max(jp_tokens, key=len)
            return candidate

    jp_tokens = _JP_TOKEN_RE.findall(s)
    if not jp_tokens:
        return s
    return max(jp_tokens, key=len)

def _dynamodb_table():
    """Get DynamoDB table handle."""
    table_name = os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
    dynamodb = boto3.resource('dynamodb')
    return dynamodb.Table(table_name)

def _exact_match_word_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Exact match lookup for WORD items by 'name' using the 'name-index' GSI.
    Returns a normalized word dict or None.
    """
    if not name:
        return None
    table = _dynamodb_table()
    response = table.query(
        IndexName='name-index',
        KeyConditionExpression='#name = :name',
        FilterExpression='PK = :pk',
        ExpressionAttributeNames={'#name': 'name'},
        ExpressionAttributeValues={':name': name, ':pk': 'WORD'}
    )
    items = response.get('Items', [])
    if not items:
        return None
    item = items[0]
    word_id = int(convert_dynamodb_value(item.get('SK', 0)) or 0)
    level = item.get('level', 0)
    level = convert_dynamodb_value(level) if level is not None else 0
    level = int(level) if isinstance(level, (int, float)) else 0
    return {
        "id": word_id,
        "name": str(item.get('name', '')),
        "hiragana": str(item.get('hiragana', '')),
        "english": str(item.get('english', '')),
        "level": level,
    }

def _exact_match_kanji_by_character(character: str) -> Optional[Dict[str, Any]]:
    """
    Exact match lookup for KANJI items by 'character' using the 'character-index' GSI.
    Returns a normalized kanji dict or None.
    """
    if not character or len(character) != 1:
        return None
    table = _dynamodb_table()
    response = table.query(
        IndexName='character-index',
        KeyConditionExpression='#character = :character',
        FilterExpression='PK = :pk',
        ExpressionAttributeNames={'#character': 'character'},
        ExpressionAttributeValues={':character': character, ':pk': 'KANJI'}
    )
    items = response.get('Items', [])
    if not items:
        return None
    item = items[0]
    kanji_id = int(convert_dynamodb_value(item.get('SK', 0)) or 0)
    return {
        "id": kanji_id,
        "kanji": str(item.get('character', '')),
        "character": str(item.get('character', '')),
        "meaning": str(item.get('english', '')),
        "reading": str(item.get('reading', item.get('onyomi', ''))),
    }

def search_word_by_name(word_name: str) -> Dict[str, Any]:
    """
    Search for a word by name with deterministic-first strategy:
    1) Extract target term from the user sentence
    2) Exact match (WORD.name)
    3) Generate variations (words only) and exact match each variation
    4) Semantic (vector) fallback across words+kanjis, returning up to 3 combined candidates
    
    This function is called by Gemini when user asks about a word.
    IMPORTANT: Semantic search results are returned as candidates (found=False) to avoid
    "nearest neighbor" mistakes being treated as exact matches.
    
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
    # Candidate selection threshold:
    # If scores are close (lower is better), return multiple candidates (up to 3).
    SCORE_DIFF_THRESHOLD = 30.0
    
    try:
        target = _extract_target_term(word_name)
        logger.info(f"Word search input='{word_name}' extracted_target='{target}'")

        # (1) Exact match (WORD.name)
        try:
            exact = _exact_match_word_by_name(target)
            if exact:
                logger.info(f"Exact word match found for '{target}': {exact.get('name')} (id={exact.get('id')})")
                return {
                    "found": True,
                    "word": {
                        "id": int(exact["id"]),
                        "name": exact["name"],
                        "hiragana": exact.get("hiragana", ""),
                        "english": exact.get("english", ""),
                        "level": int(exact.get("level", 0) or 0),
                        "detail_url": get_word_detail_url(int(exact["id"]))
                    },
                    "candidates": None,
                    "message": f"Found exact match: {exact.get('name')}"
                }
        except Exception as e:
            logger.warning(f"Exact word match failed for '{target}': {e}")

        # (2) Variations (words only) + exact match each
        try:
            variations_result = generate_word_variations_with_llm(target)
            variations = variations_result.get("variations", []) if isinstance(variations_result, dict) else []
            # Ensure deterministic order and include the original target first
            ordered = []
            for v in [target] + [str(x).strip() for x in variations if str(x).strip()]:
                if v and v not in ordered:
                    ordered.append(v)
            
            # Log the full variation list for debugging
            logger.info(f"Testing {len(ordered[:10])} variations for '{target}': {ordered[:10]}")

            for v in ordered[:10]:
                exact_v = _exact_match_word_by_name(v)
                if exact_v:
                    logger.info(f"Word match found via variation. target='{target}' matched='{v}' result='{exact_v.get('name')}'")
                    return {
                        "found": True,
                        "word": {
                            "id": int(exact_v["id"]),
                            "name": exact_v["name"],
                            "hiragana": exact_v.get("hiragana", ""),
                            "english": exact_v.get("english", ""),
                            "level": int(exact_v.get("level", 0) or 0),
                            "detail_url": get_word_detail_url(int(exact_v["id"]))
                        },
                        "candidates": None,
                        "message": f"Found exact match via variation '{v}': {exact_v.get('name')}"
                    }
                else:
                    logger.debug(f"No exact match for variation '{v}'")
        except Exception as e:
            logger.warning(f"Variation generation / exact-match loop failed for '{target}': {e}")

        # (3) Semantic fallback (vector search) across words + kanjis
        logger.info(f"No exact match found for '{target}', attempting semantic fallback")
        search_start = time.time()
        rag_service = get_rag_service()
        
        if rag_service:
            try:
                # Use search_all so we can return combined words+kanjis candidates.
                def _search_all():
                    return rag_service.search_all(target, k=10)
                
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(_search_all)
                    try:
                        all_results = future.result(timeout=20.0)
                        search_time = time.time() - search_start
                        word_results = (all_results or {}).get('words', []) or []
                        kanji_results = (all_results or {}).get('kanjis', []) or []
                        logger.info(
                            f"Semantic search completed in {search_time:.2f}s for '{target}'. "
                            f"words={len(word_results)} kanjis={len(kanji_results)}"
                        )
                        
                        # Combine results into candidates
                        combined_candidates: List[Dict[str, Any]] = []

                        for wr in word_results[:10]:
                            word_id_candidate = wr.get('id')
                            if word_id_candidate is None:
                                continue
                            level = wr.get('level', 0)
                            level = convert_dynamodb_value(level) if level is not None else 0
                            level = int(level) if isinstance(level, (int, float)) else 0
                            combined_candidates.append({
                                "type": "word",
                                "id": int(word_id_candidate),
                                "name": str(wr.get('name', '')),
                                "hiragana": str(wr.get('hiragana', '')),
                                "english": str(wr.get('english', '')),
                                "level": level,
                                "score": float(wr.get('score', float('inf'))),
                                "detail_url": get_word_detail_url(int(word_id_candidate))
                            })

                        for kr in kanji_results[:10]:
                            kanji_id_candidate = kr.get('id')
                            if kanji_id_candidate is None:
                                continue
                            kanji_char = kr.get('kanji') or kr.get('character', '')
                            combined_candidates.append({
                                "type": "kanji",
                                "id": int(kanji_id_candidate),
                                "kanji": str(kanji_char),
                                "character": str(kanji_char),
                                "meaning": str(kr.get('meaning', kr.get('english', ''))),
                                "reading": str(kr.get('reading', '')),
                                "score": float(kr.get('score', float('inf'))),
                                "detail_url": get_kanji_detail_url(int(kanji_id_candidate))
                            })

                        combined_candidates.sort(key=lambda x: x.get('score', float('inf')))
                        if not combined_candidates:
                            return {
                                "found": False,
                                "word": None,
                                "candidates": None,
                                "message": "No results found."
                            }

                        best_score = float(combined_candidates[0].get('score', float('inf')))
                        # Select up to 3 candidates only if scores are close to the best
                        top_candidates: List[Dict[str, Any]] = []
                        for c in combined_candidates:
                            if len(top_candidates) >= 3:
                                break
                            score = float(c.get('score', float('inf')))
                            if score - best_score <= SCORE_DIFF_THRESHOLD:
                                top_candidates.append(c)
                            else:
                                # Once scores diverge, stop adding more candidates
                                if top_candidates:
                                    break

                        # Ensure at least 1 candidate
                        if not top_candidates:
                            top_candidates = [combined_candidates[0]]

                        import copy
                        combined_with_type = copy.deepcopy(top_candidates)

                        word_candidates = [c for c in top_candidates if c.get('type') == 'word']
                        kanji_candidates = [c for c in top_candidates if c.get('type') == 'kanji']
                        for candidate in word_candidates:
                            candidate.pop('type', None)
                        for candidate in kanji_candidates:
                            candidate.pop('type', None)

                        return {
                            "found": False,
                            "word": None,
                            "candidates": {
                                "words": word_candidates,
                                "kanjis": kanji_candidates,
                                "combined": combined_with_type
                            },
                            "message": f"No exact match for '{target}'. Here are the closest candidates."
                        }
                    except FutureTimeoutError:
                        search_time = time.time() - search_start
                        logger.warning(f"Semantic search timed out after {search_time:.2f} seconds for '{target}'")
                        return {
                            "found": False,
                            "word": None,
                            "candidates": None,
                            "message": "I couldn't complete semantic search in time. Please provide more context (kanji spelling, meaning, or example sentence)."
                        }
            except Exception as e:
                logger.warning(f"Semantic search failed: {e}")
        
        # No semantic results or RAG init failed
        logger.warning(f"No results found for '{target}' (exact + variations + semantic)")
        return {
            "found": False,
            "word": None,
            "candidates": None,
            "message": "I couldn't find an exact match. Please provide more context (kanji spelling, meaning, or example sentence)."
        }
    
    except Exception as e:
        logger.error(f"Error searching word '{word_name}': {str(e)}")
        return {
            "found": False,
            "word": None,
            "candidates": None,
            "message": "I couldn't complete the search due to an internal error."
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
    Search for a kanji with deterministic-first strategy:
    1) Extract target term
    2) Exact match only when len(term) == 1 (KANJI.character)
    3) Semantic fallback (kanji-only) if exact match fails
    
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
        target = _extract_target_term(kanji_character)
        kanji_char = target.strip()
        logger.info(f"Kanji search input='{kanji_character}' extracted_target='{kanji_char}'")

        # (1) Exact match only for single character
        if len(kanji_char) == 1:
            try:
                exact = _exact_match_kanji_by_character(kanji_char)
                if exact:
                    return {
                        "found": True,
                        "kanji": {
                            "id": int(exact["id"]),
                            "kanji": exact["kanji"],
                            "character": exact["character"],
                            "meaning": exact.get("meaning", ""),
                            "reading": exact.get("reading", ""),
                            "detail_url": get_kanji_detail_url(int(exact["id"]))
                        },
                        "message": f"Found exact match: {kanji_char}"
                    }
            except Exception as e:
                logger.warning(f"Exact kanji match failed for '{kanji_char}': {e}")
        else:
            return {
                "found": False,
                "kanji": None,
                "message": "Exact kanji lookup only supports a single character. This looks like a word/phrase; try word search."
            }

        # (2) Semantic fallback (kanji-only)
        rag_service = get_rag_service()
        if rag_service:
            try:
                vector_results = rag_service.search_kanjis(kanji_char, k=3)
                if vector_results:
                    best_match = vector_results[0]
                    kanji_id = best_match.get('id')
                    if kanji_id is not None:
                        best_char = best_match.get('kanji') or best_match.get('character', kanji_char)
                        return {
                            "found": False,
                            "kanji": None,
                            "candidates": [
                                {
                                    "id": int(kanji_id),
                                    "kanji": str(best_char),
                                    "character": str(best_char),
                                    "meaning": str(best_match.get('meaning', best_match.get('english', ''))),
                                    "reading": str(best_match.get('reading', '')),
                                    "score": float(best_match.get('score', float('inf'))),
                                    "detail_url": get_kanji_detail_url(int(kanji_id))
                                }
                            ],
                            "message": f"No exact match for '{kanji_char}'. Here is the closest candidate."
                        }
            except Exception as e:
                logger.warning(f"Semantic kanji search failed: {e}")

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

# Cache for word variations (thread-safe)
_variation_cache: Dict[str, Dict[str, Any]] = {}
_cache_lock = threading.Lock()
_MAX_CACHE_SIZE = 100

def _cache_variations(word_name: str, variations: Dict[str, Any]):
    """Cache word variations with size limit (FIFO)"""
    with _cache_lock:
        _variation_cache[word_name] = variations
        # Limit cache size
        if len(_variation_cache) > _MAX_CACHE_SIZE:
            # Remove oldest entry (FIFO)
            oldest_key = next(iter(_variation_cache))
            del _variation_cache[oldest_key]
            logger.debug(f"Cache limit reached, removed oldest entry: {oldest_key}")

def _get_cached_variations(word_name: str) -> Optional[Dict[str, Any]]:
    """Get cached variations if available"""
    with _cache_lock:
        return _variation_cache.get(word_name)

def generate_word_variations_with_llm(word_name: str) -> Dict[str, Any]:
    """
    Generate word variations (conjugations, writing forms, politeness levels) using LLM
    
    This function uses Gemini LLM to generate various forms of a Japanese word including:
    - Conjugation forms (ます形, 過去形, て形, 否定形)
    - Part-of-speech variations (verb → noun, etc.)
    - Writing variations (kanji ↔ hiragana)
    - Politeness levels (casual ↔ polite)
    
    Args:
        word_name: The word name to generate variations for (e.g., '戦う')
    
    Returns:
        {
            "variations": List[str],  # List of word variations
            "reasoning": str,  # Brief explanation of why these variations were generated
            "confidence": float  # Confidence score (0.0-1.0)
        }
    """
    # Check cache first
    cached = _get_cached_variations(word_name)
    if cached:
        logger.info(f"Using cached variations for '{word_name}'")
        return cached
    
    try:
        # Import here to avoid circular dependency
        try:
            from integrations.gemini_client import GeminiClient
        except ImportError:
            from app.api.v1.chat.integrations.gemini_client import GeminiClient
        
        client = GeminiClient()
        
        # Generate variations with timeout
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                client.generate_word_variations,
                word_name,
                lang="ja",
                max_variations=10
            )
            try:
                result = future.result(timeout=5.0)  # 5 second timeout
                
                # Cache the result
                _cache_variations(word_name, result)
                
                logger.info(f"Generated {len(result.get('variations', []))} variations for '{word_name}'")
                return result
            
            except FutureTimeoutError:
                logger.warning(f"Variation generation timed out for '{word_name}'")
                return {
                    "variations": [],
                    "reasoning": "Generation timed out",
                    "confidence": 0.0
                }
    
    except Exception as e:
        logger.error(f"Error generating variations for '{word_name}': {str(e)}")
        return {
            "variations": [],
            "reasoning": f"Error: {str(e)}",
            "confidence": 0.0
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
    },
    "generate_word_variations_with_llm": {
        "function": generate_word_variations_with_llm,
        "description": "Generate word variations (conjugations, writing forms, politeness levels) for a Japanese word using AI. Use this when search_word_by_name returns found=False. This will generate variations like: ます形, 過去形, kanji/hiragana variations, etc. Then use search_word_by_name again with the generated variations to find the word.",
        "parameters": {
            "type": "object",
            "properties": {
                "word_name": {
                    "type": "string",
                    "description": "The word name to generate variations for (e.g., '戦う')"
                }
            },
            "required": ["word_name"]
        }
    }
}

