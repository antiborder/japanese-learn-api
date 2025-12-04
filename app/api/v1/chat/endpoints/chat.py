from fastapi import APIRouter, HTTPException, Depends, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from schemas.chat import ChatMessageRequest, ChatMessageResponse
from integrations.gemini_client import GeminiClient
from services.conversation_logger import ConversationLogger
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
    Simple text chat endpoint
    No RAG, no DB access, just direct Gemini API call
    
    Authentication: Optional
    - If Authorization header is provided and valid, user_id will be set
    - If no header or invalid token, user_id will be None (anonymous access)
    - Anonymous users can still use the chatbot
    """
    try:
        client = GeminiClient()
        
        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Use user_id if authenticated, otherwise use anonymous identifier
        effective_user_id = user_id if user_id else f"anonymous-{session_id}"
        logger.info(f"Chat request from user: {effective_user_id}")
        
        # Call Gemini API
        response_text = client.chat(request.message)
        
        # Log conversation (non-blocking, errors don't fail the request)
        try:
            conversation_logger.log_conversation(
                user_id=effective_user_id,
                session_id=session_id,
                question=request.message,
                response=response_text,
                message_type="text"
            )
        except Exception as e:
            logger.warning(f"Failed to log conversation: {e}")
            # Continue even if logging fails
        
        return ChatMessageResponse(
            response=response_text,
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

