import logging
import os
import requests
from integrations.dynamodb_integration import save_contact, check_rate_limit
from integrations.ses_integration import send_contact_notification

logger = logging.getLogger(__name__)

RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", "")
RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


def verify_recaptcha(token: str) -> bool:
    try:
        resp = requests.post(
            RECAPTCHA_VERIFY_URL,
            data={"secret": RECAPTCHA_SECRET_KEY, "response": token},
            timeout=5,
        )
        result = resp.json()
        return result.get("success", False) and result.get("score", 0) >= 0.5
    except Exception as e:
        logger.error(f"reCAPTCHA verification failed: {e}")
        return False


def submit_contact(
    category: str,
    email: str,
    subject: str,
    body: str,
    lang: str,
    is_authenticated: bool,
    recaptcha_token: str | None,
    client_ip: str,
) -> str:
    # レートリミットチェック（未ログインユーザーのみ）
    if not is_authenticated:
        if not check_rate_limit(client_ip):
            raise ValueError("rate_limit_exceeded")

        # reCAPTCHA 検証（未ログインユーザーのみ）
        if not recaptcha_token or not verify_recaptcha(recaptcha_token):
            raise ValueError("recaptcha_failed")

    contact_id = save_contact(category, email, subject, body, lang, is_authenticated)
    send_contact_notification(contact_id, category, email, subject, body, lang)
    return contact_id
