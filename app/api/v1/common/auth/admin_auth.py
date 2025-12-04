"""
Admin authentication utilities
Checks if user has admin role/group in Cognito
"""
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

# Admin email list - can be configured via environment variable or hardcoded
ADMIN_EMAILS = os.environ.get("ADMIN_EMAILS", "").split(",") if os.environ.get("ADMIN_EMAILS") else []
# Remove empty strings
ADMIN_EMAILS = [email.strip() for email in ADMIN_EMAILS if email.strip()]

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

def require_admin_role(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """
    Verify JWT token and check if user has admin role
    Returns user_id (email) if admin, raises 403 if not admin, 401 if not authenticated
    
    Admin check methods (in order of priority):
    1. Check if user email is in ADMIN_EMAILS environment variable
    2. Check if token has 'cognito:groups' claim with 'admin' group
    3. Check if token has custom 'admin' claim
    """
    token = credentials.credentials
    
    try:
        jwks = get_jwks()
        
        # Decode and validate token
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=COGNITO_ISSUER,
            options={"verify_at_hash": False}
        )
        
        user_email = payload.get("email")
        if not user_email:
            logger.warning("No email found in token payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user email"
            )
        
        # Check if user is admin
        is_admin = False
        
        # Method 1: Check ADMIN_EMAILS list
        if ADMIN_EMAILS and user_email in ADMIN_EMAILS:
            is_admin = True
            logger.info(f"User {user_email} is admin (via ADMIN_EMAILS)")
        
        # Method 2: Check Cognito groups
        if not is_admin:
            groups = payload.get("cognito:groups", [])
            if isinstance(groups, list) and "admin" in groups:
                is_admin = True
                logger.info(f"User {user_email} is admin (via Cognito group)")
        
        # Method 3: Check custom admin claim
        if not is_admin:
            if payload.get("admin") == True or payload.get("custom:admin") == "true":
                is_admin = True
                logger.info(f"User {user_email} is admin (via custom claim)")
        
        if not is_admin:
            logger.warning(f"User {user_email} attempted to access admin endpoint but is not admin")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        return user_email
        
    except HTTPException:
        raise
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    except Exception as e:
        logger.error(f"Unexpected error during admin authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

