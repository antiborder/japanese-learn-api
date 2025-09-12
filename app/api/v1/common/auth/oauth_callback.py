import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status, Depends
from fastapi.responses import RedirectResponse
import requests
from jose import jwt, JWTError
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# OAuth設定
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/callback")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

@router.get("/auth/google")
async def google_auth():
    """
    Google OAuth認証の開始
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid email profile&"
        f"access_type=offline"
    )
    
    return RedirectResponse(url=auth_url)

@router.get("/auth/callback")
async def oauth_callback(
    code: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    state: Optional[str] = Query(None)
):
    """
    OAuth認証のコールバック処理
    """
    if error:
        logger.error(f"OAuth error: {error}")
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/error?error={error}")
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
    
    try:
        # アクセストークンを取得
        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI,
            }
        )
        token_response.raise_for_status()
        token_data = token_response.json()
        
        # IDトークンからユーザー情報を取得
        id_token = token_data.get("id_token")
        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID token not received"
            )
        
        # IDトークンを検証（簡易版）
        # 本番環境では適切な検証が必要
        user_info = jwt.get_unverified_claims(id_token)
        email = user_info.get("email")
        name = user_info.get("name")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in token"
            )
        
        # フロントエンドにリダイレクト（トークンを含む）
        # 本番環境では適切なセキュリティ対策が必要
        redirect_url = f"{FRONTEND_URL}/auth/success?token={id_token}&email={email}&name={name}"
        return RedirectResponse(url=redirect_url)
        
    except requests.RequestException as e:
        logger.error(f"Token exchange failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token exchange failed"
        )
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

# get_user_info関数は別途定義するか、必要に応じて削除 