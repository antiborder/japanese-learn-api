from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from schemas.chat import ChatMessageRequest, ChatMessageResponse
from integrations.gemini_client import GeminiClient
from services.conversation_logger import ConversationLogger
from tools.dynamodb_tools import TOOL_FUNCTIONS  # Import tool functions
import logging
import uuid
import os
import requests
from jose import jwt, JWTError

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize conversation logger
conversation_logger = ConversationLogger()

bearer_scheme = HTTPBearer()

COGNITO_REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "ap-northeast-1_WGOHW5Nx9")
COGNITO_APP_CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID", "6kkiqk3qqjnisn96rgc3kne63p")
COGNITO_ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
COGNITO_JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"
_jwks = None

def get_jwks():
    global _jwks
    if _jwks is None:
        resp = requests.get(COGNITO_JWKS_URL)
        resp.raise_for_status()
        _jwks = resp.json()
    return _jwks

def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> str:
    token = credentials.credentials
    try:
        jwks = get_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=COGNITO_ISSUER,
            options={"verify_at_hash": False}
        )
        user_id = payload.get("email")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing user ID")
        return user_id
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(
    request: ChatMessageRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Chat endpoint with tool calling support
    - If user asks about a word/kanji, tool functions will be called
    - Tool functions return data + detail page URLs
    - Gemini includes links in its response

    Authentication: Required
    - A valid Cognito JWT must be provided in the Authorization header
    """
    try:
        client = GeminiClient()

        # Register tools for function calling
        client.register_tools(TOOL_FUNCTIONS)

        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())

        effective_user_id = user_id
        logger.info(f"Chat request from user: {effective_user_id}, message: {request.message}")
        
        # Retrieve conversation history for this session
        conversation_history = None
        if session_id:
            try:
                logger.info(f"Attempting to retrieve conversation history for session {session_id}")
                history = conversation_logger.get_conversation_history(session_id, limit=10)
                if history:
                    conversation_history = history
                    logger.info(f"Retrieved {len(history)} messages from conversation history for session {session_id}")
                else:
                    logger.info(f"No conversation history found for session {session_id} (this is expected for first message)")
            except Exception as e:
                logger.warning(f"Failed to retrieve conversation history: {e}", exc_info=True)
                # Continue without history - don't fail the request
        
        import time
        request_start = time.time()
        
        # Call Gemini API with tool support (using iterative method for multi-step tool chaining)
        lang = request.lang or "ja"  # Ensure lang is never None
        logger.info(f"Calling Gemini API with tools (iterative, lang={lang})...")
        gemini_start = time.time()
        result = client.chat_with_tools_iterative(
            request.message,
            conversation_history=conversation_history,
            tool_functions=TOOL_FUNCTIONS,
            max_iterations=5,
            lang=lang
        )
        gemini_time = time.time() - gemini_start
        iterations = result.get("iterations", 0)
        logger.info(f"Gemini API call completed in {gemini_time:.2f} seconds ({iterations} iterations)")
        
        response_text = result["response"]
        
        # Log tool calls if any
        if result.get("tool_calls"):
            logger.info(f"Tool calls made ({len(result['tool_calls'])} total): {result['tool_calls']}")
        else:
            logger.warning(f"No tool calls made for message: {request.message}")
        
        # Log tool results if any
        if result.get("tool_results"):
            logger.info(f"Tool results: {result['tool_results']}")
            # Debug: log structure of each tool result
            for i, tr in enumerate(result["tool_results"]):
                logger.info(f"Tool result {i}: {tr}")
                if "result" in tr:
                    logger.info(f"  Result keys: {tr['result'].keys() if isinstance(tr['result'], dict) else 'not a dict'}")
                    if isinstance(tr["result"], dict) and "candidates" in tr["result"]:
                        logger.info(f"  Candidates keys: {tr['result']['candidates'].keys() if isinstance(tr['result']['candidates'], dict) else 'not a dict'}")
        else:
            logger.warning("No tool results returned")
        
        # Extract word_ids and kanji_ids from tool_results
        word_ids = []
        kanji_ids = []
        
        if result.get("tool_results"):
            logger.info(f"Processing {len(result['tool_results'])} tool results")
            for i, tool_result in enumerate(result["tool_results"]):
                logger.info(f"Tool result {i}: name={tool_result.get('name')}, keys={list(tool_result.keys()) if isinstance(tool_result, dict) else 'not a dict'}")
                
                if "error" in tool_result:
                    logger.warning(f"Tool result {i} has error: {tool_result.get('error')}")
                    # Skip results with errors
                    continue
                
                result_data = tool_result.get("result", {})
                logger.info(f"Processing tool result {i} data: {list(result_data.keys()) if isinstance(result_data, dict) else 'not a dict'}")
                logger.info(f"Tool result {i} full data: {result_data}")
                
                # Extract word IDs from direct match
                if "word" in result_data and result_data.get("word"):
                    word = result_data["word"]
                    logger.info(f"Found word in result {i}: {word}")
                    if "id" in word:
                        word_id = word["id"]
                        if word_id not in word_ids:
                            word_ids.append(word_id)
                            logger.info(f"Added word_id: {word_id}")
                    else:
                        logger.warning(f"Word in result {i} has no 'id' field: {word.keys() if isinstance(word, dict) else 'not a dict'}")
                
                # Extract kanji IDs from direct match
                if "kanji" in result_data and result_data.get("kanji"):
                    kanji = result_data["kanji"]
                    logger.info(f"Found kanji in result {i}: {kanji}")
                    if "id" in kanji:
                        kanji_id = kanji["id"]
                        if kanji_id not in kanji_ids:
                            kanji_ids.append(kanji_id)
                            logger.info(f"Added kanji_id: {kanji_id}")
                    else:
                        logger.warning(f"Kanji in result {i} has no 'id' field: {kanji.keys() if isinstance(kanji, dict) else 'not a dict'}")
                
                # Extract IDs from candidates (when found=false, candidates are returned)
                if "candidates" in result_data and result_data.get("candidates"):
                    candidates = result_data["candidates"]
                    logger.info(f"Found candidates: {list(candidates.keys()) if isinstance(candidates, dict) else 'not a dict'}")
                    
                    # Extract from combined list (preferred - contains top 3 candidates sorted by score)
                    if "combined" in candidates and candidates.get("combined"):
                        logger.info(f"Extracting from combined list: {len(candidates['combined'])} candidates")
                        for candidate in candidates["combined"]:
                            candidate_type = candidate.get("type")
                            candidate_id = candidate.get("id")
                            logger.info(f"  Candidate: type={repr(candidate_type)}, id={candidate_id}, full candidate: {candidate}")
                            if candidate_id is not None:
                                if candidate_type == "word" and candidate_id not in word_ids:
                                    word_ids.append(candidate_id)
                                    logger.info(f"  Added word_id: {candidate_id}")
                                elif candidate_type == "kanji" and candidate_id not in kanji_ids:
                                    kanji_ids.append(candidate_id)
                                    logger.info(f"  Added kanji_id: {candidate_id}")
                                else:
                                    logger.warning(f"  Skipped candidate: type={repr(candidate_type)}, id={candidate_id}")
                    
                    # Also extract from separate words and kanjis lists as fallback/backup
                    # This ensures we get IDs even if combined list doesn't have type field
                    if "words" in candidates and candidates.get("words"):
                        logger.info(f"Extracting from words list: {len(candidates['words'])} word candidates")
                        for word_candidate in candidates["words"]:
                            word_id = word_candidate.get("id")
                            if word_id is not None and word_id not in word_ids:
                                word_ids.append(word_id)
                                logger.info(f"  Added word_id from words list: {word_id}")
                    
                    if "kanjis" in candidates and candidates.get("kanjis"):
                        logger.info(f"Extracting from kanjis list: {len(candidates['kanjis'])} kanji candidates")
                        for kanji_candidate in candidates["kanjis"]:
                            kanji_id = kanji_candidate.get("id")
                            if kanji_id is not None and kanji_id not in kanji_ids:
                                kanji_ids.append(kanji_id)
                                logger.info(f"  Added kanji_id from kanjis list: {kanji_id}")
        
        logger.info(f"Extracted word_ids: {word_ids}, kanji_ids: {kanji_ids}")
        
        # Log conversation (non-blocking, errors don't fail the request)
        try:
            conversation_logger.log_conversation(
                user_id=effective_user_id,
                session_id=session_id,
                question=request.message,
                response=response_text,
                message_type="text",
                metadata={
                    "tool_calls": result.get("tool_calls", []),
                    "tool_results": result.get("tool_results", []),
                    "word_ids": word_ids,
                    "kanji_ids": kanji_ids
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log conversation: {e}")
            # Continue even if logging fails
        
        # Build response with optional word_ids and kanji_ids
        response_data = {
            "response": response_text,
            "session_id": session_id
        }
        
        # Always include word_ids and kanji_ids (even if empty, to distinguish from null)
        # Frontend expects these fields to be present
        response_data["word_ids"] = word_ids if word_ids else None
        response_data["kanji_ids"] = kanji_ids if kanji_ids else None
        
        logger.info(f"Final response - word_ids: {response_data.get('word_ids')}, kanji_ids: {response_data.get('kanji_ids')}")
        
        return ChatMessageResponse(**response_data)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error in chat endpoint: {str(e)}")
        logger.error(f"Traceback: {error_traceback}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

