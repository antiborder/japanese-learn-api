from fastapi import APIRouter, HTTPException, Depends, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from schemas.chat import ChatMessageRequest, ChatMessageResponse
from integrations.gemini_client import GeminiClient
from services.conversation_logger import ConversationLogger
from tools.dynamodb_tools import TOOL_FUNCTIONS  # Import tool functions
from typing import Optional
import logging
import uuid
import os
import requests
from jose import jwt, JWTError

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize conversation logger
conversation_logger = ConversationLogger()

# Optional bearer scheme - doesn't auto-raise on missing token
optional_bearer_scheme = HTTPBearer(auto_error=False)

def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(optional_bearer_scheme)
) -> Optional[str]:
    """
    Optional authentication - returns user_id if token is valid, None otherwise
    Allows anonymous users to use the chatbot
    """
    if not credentials:
        logger.info("No authorization header - allowing anonymous access")
        return None
    
    # Try to validate the token
    try:
        token = credentials.credentials
        
        # Get Cognito configuration
        cognito_region = os.environ.get("AWS_REGION", "ap-northeast-1")
        cognito_user_pool_id = os.environ.get("COGNITO_USER_POOL_ID", "ap-northeast-1_WGOHW5Nx9")
        cognito_app_client_id = os.environ.get("COGNITO_APP_CLIENT_ID", "6kkiqk3qqjnisn96rgc3kne63p")
        cognito_issuer = f"https://cognito-idp.{cognito_region}.amazonaws.com/{cognito_user_pool_id}"
        cognito_jwks_url = f"{cognito_issuer}/.well-known/jwks.json"
        
        # Get JWKS
        resp = requests.get(cognito_jwks_url)
        resp.raise_for_status()
        jwks = resp.json()
        
        # Decode and validate token
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=cognito_app_client_id,
            issuer=cognito_issuer,
            options={"verify_at_hash": False}
        )
        
        user_id = payload.get("email")
        if user_id:
            logger.info(f"Authenticated user: {user_id}")
            return user_id
        else:
            logger.warning("No email found in token payload - allowing anonymous access")
            return None
            
    except JWTError as e:
        logger.info(f"JWT validation failed: {e} - allowing anonymous access")
        return None
    except Exception as e:
        logger.warning(f"Error validating token: {e} - allowing anonymous access")
        return None

@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(
    request: ChatMessageRequest,
    user_id: Optional[str] = Depends(get_optional_user_id)
):
    """
    Chat endpoint with tool calling support
    - If user asks about a word/kanji, tool functions will be called
    - Tool functions return data + detail page URLs
    - Gemini includes links in its response
    
    Authentication: Optional
    - If Authorization header is provided and valid, user_id will be set
    - If no header or invalid token, user_id will be None (anonymous access)
    - Anonymous users can still use the chatbot
    """
    try:
        client = GeminiClient()
        
        # Register tools for function calling
        client.register_tools(TOOL_FUNCTIONS)
        
        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Use user_id if authenticated, otherwise use anonymous identifier
        effective_user_id = user_id if user_id else f"anonymous-{session_id}"
        logger.info(f"Chat request from user: {effective_user_id}, message: {request.message}")
        
        import time
        request_start = time.time()
        
        # Call Gemini API with tool support
        logger.info("Calling Gemini API with tools...")
        gemini_start = time.time()
        result = client.chat_with_tools(
            request.message,
            tool_functions=TOOL_FUNCTIONS
        )
        gemini_time = time.time() - gemini_start
        logger.info(f"Gemini API call completed in {gemini_time:.2f} seconds")
        
        response_text = result["response"]
        
        # Log tool calls if any
        if result.get("tool_calls"):
            logger.info(f"Tool calls made: {result['tool_calls']}")
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
                            logger.info(f"  Candidate: type={candidate_type}, id={candidate_id}")
                            if candidate_id:
                                if candidate_type == "word" and candidate_id not in word_ids:
                                    word_ids.append(candidate_id)
                                    logger.info(f"  Added word_id: {candidate_id}")
                                elif candidate_type == "kanji" and candidate_id not in kanji_ids:
                                    kanji_ids.append(candidate_id)
                                    logger.info(f"  Added kanji_id: {candidate_id}")
                    else:
                        # Fallback: extract from separate words and kanjis lists
                        logger.info("Extracting from separate words/kanjis lists")
                        if "words" in candidates and candidates.get("words"):
                            for word_candidate in candidates["words"]:
                                word_id = word_candidate.get("id")
                                if word_id and word_id not in word_ids:
                                    word_ids.append(word_id)
                                    logger.info(f"  Added word_id from words list: {word_id}")
                        
                        if "kanjis" in candidates and candidates.get("kanjis"):
                            for kanji_candidate in candidates["kanjis"]:
                                kanji_id = kanji_candidate.get("id")
                                if kanji_id and kanji_id not in kanji_ids:
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

