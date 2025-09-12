import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status, Request
from fastapi.responses import JSONResponse
import requests
from jose import jwt, JWTError
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Cognito設定
COGNITO_REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "ap-northeast-1_WGOHW5Nx9")
COGNITO_APP_CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID", "6kkiqk3qqjnisn96rgc3kne63p")
# パブリッククライアントなのでクライアントシークレットは不要
COGNITO_DOMAIN = os.environ.get("COGNITO_DOMAIN", "https://nihongo.auth.ap-northeast-1.amazoncognito.com")

# フロントエンド設定
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
COGNITO_REDIRECT_URI = os.environ.get("COGNITO_REDIRECT_URI", f"{FRONTEND_URL}/callback")

@router.get("/oauth/google")
async def google_auth():
    """
    Cognito経由でGoogle OAuth認証を開始
    """
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
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@router.get("/oauth/callback")
async def oauth_callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None)
):
    """
    Cognito OAuth認証のコールバック処理
    エンドポイント: GET /api/v1/auth/oauth/callback?code={auth_code}&state={state}
    レスポンス形式: JSON（リダイレクト禁止）
    """
    # CORSプリフライトリクエストの場合はOPTIONSレスポンスを返す
    if request.method == "OPTIONS":
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
    
    # エラーレスポンス（HTTP 400）
    if error:
        logger.error(f"OAuth error: {error} - {error_description}")
        error_message = error_description or error
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": error_message
            },
            headers={
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    
    # 認証コードが無い場合のエラーレスポンス（HTTP 400）
    if not code:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "認証コードが無効です"
            },
            headers={
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    
    try:
        # Cognitoからアクセストークンを取得（パブリッククライアント用）
        token_response = requests.post(
            f"{COGNITO_DOMAIN}/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "client_id": COGNITO_APP_CLIENT_ID,
                "code": code,
                "redirect_uri": COGNITO_REDIRECT_URI,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
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
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:3000",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        # IDトークンを検証してユーザー情報を取得
        try:
            # CognitoのIDトークンを検証（簡易版）
            # 本番環境では適切な検証が必要
            user_info = jwt.get_unverified_claims(id_token)
            email = user_info.get("email")
            name = user_info.get("name")
            user_id = user_info.get("sub")  # CognitoのユーザーID
            
            if not email:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "ユーザー情報の取得に失敗しました"
                    },
                    headers={
                        "Access-Control-Allow-Origin": "http://localhost:3000",
                        "Access-Control-Allow-Credentials": "true",
                    }
                )
            
            # 成功レスポンス（HTTP 200）
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "token": id_token,
                    "user": {
                        "id": user_id,  # CognitoのユーザーIDを使用
                        "email": email,
                        "name": name or email,
                        "is_active": True
                    }
                },
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:3000",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
            
        except JWTError as e:
            logger.error(f"JWT decode error: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "ユーザー情報の取得に失敗しました"
                },
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:3000",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
    except requests.RequestException as e:
        logger.error(f"Token exchange failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "アクセストークンの取得に失敗しました"
            },
            headers={
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "データベースエラーが発生しました"
            },
            headers={
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Credentials": "true",
            }
        )

@router.options("/oauth/callback")
async def oauth_callback_options():
    """
    CORSプリフライトリクエスト用のOPTIONSハンドラー
    """
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