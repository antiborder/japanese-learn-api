import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status, Request
from fastapi.responses import JSONResponse
import requests
from jose import jwt, JWTError

logger = logging.getLogger(__name__)

router = APIRouter()

# Cognito設定
COGNITO_REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "ap-northeast-1_WGOHW5Nx9")
COGNITO_APP_CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID", "6kkiqk3qqjnisn96rgc3kne63p")
COGNITO_DOMAIN = os.environ.get("COGNITO_DOMAIN", "https://nihongo.auth.ap-northeast-1.amazoncognito.com")

# フロントエンド設定
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
COGNITO_REDIRECT_URI = os.environ.get("COGNITO_REDIRECT_URI", f"{FRONTEND_URL}/callback/")


@router.get("/oauth/google")
async def google_auth():
    """Cognito経由でGoogle OAuth認証を開始"""
    auth_url = (
        f"{COGNITO_DOMAIN}/oauth2/authorize?"
        f"response_type=code&"
        f"client_id={COGNITO_APP_CLIENT_ID}&"
        f"redirect_uri={COGNITO_REDIRECT_URI}&"
        f"scope=openid+email+profile&"
        f"identity_provider=Google"
    )
    
    return JSONResponse(
        status_code=200,
        content={"auth_url": auth_url},
        headers={}
    )

@router.get("/oauth/callback")
async def oauth_callback(
    request: Request,
    code: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None)
):
    """Cognito OAuth認証のコールバック処理"""
    
    # 動的にリダイレクトURIを決定
    origin = request.headers.get("origin") or request.headers.get("referer")
    if origin and "localhost" in origin:
        redirect_uri = "http://localhost:3000/callback/"
    else:
        redirect_uri = "https://nihongo.cloud/callback/"
    
    logger.info(f"Using redirect_uri: {redirect_uri}")
    
    # エラーレスポンス
    if error:
        logger.error(f"OAuth error: {error} - {error_description}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": error_description or error
            },
            headers={}
        )
    
    # 認証コードが無い場合
    if not code:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "認証コードが無効です"
            },
            headers={}
        )
    
    try:
        # Cognitoからアクセストークンを取得
        token_response = requests.post(
            f"{COGNITO_DOMAIN}/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "client_id": COGNITO_APP_CLIENT_ID,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # エラーレスポンスの詳細をログに出力
        if token_response.status_code != 200:
            logger.error(f"Cognito token exchange failed: {token_response.status_code}")
            logger.error(f"Response content: {token_response.text}")
            logger.error(f"Request data: grant_type=authorization_code, client_id={COGNITO_APP_CLIENT_ID}, code={code[:10]}..., redirect_uri={redirect_uri}")
        
        token_response.raise_for_status()
        token_data = token_response.json()
        
        # IDトークンを取得
        id_token = token_data.get("id_token")
        if not id_token:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "アクセストークンの取得に失敗しました"
                },
                headers={}
            )
        
        # IDトークンからユーザー情報を取得
        user_info = jwt.get_unverified_claims(id_token)
        email = user_info.get("email")
        name = user_info.get("name")
        user_id = user_info.get("sub")
        
        if not email:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "ユーザー情報の取得に失敗しました"
                },
                headers={}
            )
        
        # 成功レスポンス
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "token": id_token,
                "user": {
                    "id": user_id,
                    "email": email,
                    "name": name or email,
                    "is_active": True
                }
            },
            headers={}
        )
        
    except (requests.RequestException, JWTError) as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "認証処理中にエラーが発生しました"
            },
            headers={}
        )

@router.options("/oauth/callback")
async def oauth_callback_options():
    """CORSプリフライトリクエスト用のOPTIONSハンドラー"""
    return JSONResponse(
        status_code=200,
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
        }
    )