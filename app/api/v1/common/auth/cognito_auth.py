import os
import requests
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

COGNITO_REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "ap-northeast-1_WGOHW5Nx9")
COGNITO_APP_CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID", "6kkiqk3qqjnisn96rgc3kne63p")
COGNITO_ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
COGNITO_JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"

bearer_scheme = HTTPBearer()
_jwks = None

def get_jwks():
    global _jwks
    if _jwks is None:
        try:
            resp = requests.get(COGNITO_JWKS_URL)
            resp.raise_for_status()
            _jwks = resp.json()
        except Exception as e:
            logger.error(f"Failed to load JWKS: {e}")
            raise
    return _jwks

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """
    JWTトークンを検証し、ユーザーID（sub）を返す
    認証失敗時は401エラーを返す
    """
    token = credentials.credentials
    
    try:
        jwks = get_jwks()
        
        # at_hashクレームの検証を無効にする
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=COGNITO_ISSUER,
            options={"verify_at_hash": False}  # at_hashの検証を無効化
        )
        
        user_id = payload.get("email")
        if not user_id:
            logger.warning("No email found in token payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        
        return user_id
        
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        ) 