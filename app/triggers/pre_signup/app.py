"""Cognito Pre sign-up トリガー

ボットが他人のメールアドレスで SignUp API を叩き、検証メールがスパム報告される問題への対策。
フロントエンドが validationData.recaptchaToken に載せた reCAPTCHA v3 トークンを検証し、
失敗した場合は例外を投げて Cognito にユーザー作成（＝検証メール送信）を拒否させる。
"""

import json
import logging
import os
import urllib.parse
import urllib.request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", "")
RECAPTCHA_MIN_SCORE = float(os.environ.get("RECAPTCHA_MIN_SCORE", "0.5"))
RECAPTCHA_ACTION = "signup"


def verify_recaptcha(token: str) -> bool:
    data = urllib.parse.urlencode({"secret": RECAPTCHA_SECRET_KEY, "response": token}).encode()
    try:
        # Cognito のトリガーは 5 秒でタイムアウトするため短めに設定
        with urllib.request.urlopen(RECAPTCHA_VERIFY_URL, data=data, timeout=3) as resp:
            result = json.loads(resp.read())
    except Exception as e:
        logger.error(f"reCAPTCHA verification request failed: {e}")
        return False

    ok = (
        result.get("success", False)
        and result.get("action") == RECAPTCHA_ACTION
        and result.get("score", 0) >= RECAPTCHA_MIN_SCORE
    )
    if not ok:
        logger.warning(
            "reCAPTCHA rejected: success=%s action=%s score=%s errors=%s",
            result.get("success"),
            result.get("action"),
            result.get("score"),
            result.get("error-codes"),
        )
    return ok


def lambda_handler(event, context):
    # Google ログイン（PreSignUp_ExternalProvider）や管理者作成はボット対策の対象外
    if event.get("triggerSource") != "PreSignUp_SignUp":
        return event

    if not RECAPTCHA_SECRET_KEY:
        logger.warning("RECAPTCHA_SECRET_KEY is not set; skipping reCAPTCHA verification")
        return event

    token = (event["request"].get("validationData") or {}).get("recaptchaToken")
    if not token or not verify_recaptcha(token):
        # Cognito はこのメッセージを UserLambdaValidationException としてクライアントに返す
        raise Exception("recaptcha_failed")

    return event
