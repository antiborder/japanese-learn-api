import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from typing import Optional
from schemas.contact import ContactRequest, ContactResponse
from services.contact_service import submit_contact

logger = logging.getLogger(__name__)
router = APIRouter()

_bearer = HTTPBearer(auto_error=False)


def _get_optional_email(credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer)) -> Optional[str]:
    """JWTが存在すれば email を返す。なければ None（エラーにしない）"""
    if credentials is None:
        return None
    try:
        import os
        import requests as req
        from jose import jwt

        token = credentials.credentials
        region = os.environ.get("AWS_REGION", "ap-northeast-1")
        pool_id = os.environ.get("COGNITO_USER_POOL_ID", "")
        client_id = os.environ.get("COGNITO_APP_CLIENT_ID", "")
        issuer = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"
        jwks = req.get(f"{issuer}/.well-known/jwks.json").json()
        payload = jwt.decode(
            token, jwks, algorithms=["RS256"], audience=client_id, issuer=issuer, options={"verify_at_hash": False}
        )
        return payload.get("email")
    except Exception:
        return None


@router.post("/", response_model=ContactResponse, status_code=201)
async def submit_contact_form(
    body: ContactRequest,
    request: Request,
    authenticated_email: Optional[str] = Depends(_get_optional_email),
):
    # Honeypot チェック
    if body.honeypot:
        return ContactResponse(message="submitted")

    is_authenticated = authenticated_email is not None
    # ログイン済みの場合はトークンのメールアドレスを優先
    email = authenticated_email if is_authenticated else str(body.email)

    client_ip = (
        request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        .split(",")[0]
        .strip()
    )

    try:
        submit_contact(
            category=body.category.value,
            email=email,
            subject=body.subject,
            body=body.body,
            lang=body.lang,
            is_authenticated=is_authenticated,
            recaptcha_token=body.recaptcha_token,
            client_ip=client_ip,
        )
    except ValueError as e:
        msg = str(e)
        if msg == "rate_limit_exceeded":
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
        if msg == "recaptcha_failed":
            raise HTTPException(status_code=400, detail="reCAPTCHA verification failed.")
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        logger.error(f"Contact submission error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return ContactResponse(message="submitted")
