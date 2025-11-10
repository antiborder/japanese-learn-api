import logging
from fastapi import APIRouter, HTTPException, Path

from schemas.attempt import KanaAttemptRequest, KanaAttemptResponse
from services.learning_service import LearningService

logger = logging.getLogger(__name__)

router = APIRouter()
learning_service = LearningService()


@router.post("/users/{user_id}/attempts", response_model=KanaAttemptResponse)
async def record_kana_attempt(
    user_id: str = Path(..., description="ユーザーID"),
    request: KanaAttemptRequest = ...,
):
    """
    かなレッスンの学習履歴を記録します。

    Args:
        user_id: ユーザーID
        request: 学習履歴リクエスト

    Returns:
        KanaAttemptResponse: 記録結果
    """
    try:
        logger.info(
            "Recording kana attempt for user %s, char %s", user_id, request.char
        )
        result = await learning_service.record_learning(
            user_id=user_id,
            char=request.char,
            level=request.level,
            confidence=request.confidence,
            time=request.time,
        )
        logger.info(
            "Successfully recorded kana attempt for user %s, char %s",
            user_id,
            request.char,
        )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "Error recording kana attempt for user %s, char %s", user_id, request.char
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post(
    "/test/users/{user_id}/attempts",
    response_model=KanaAttemptResponse,
    summary="テスト用：トークン無しでかなレッスン結果を保存",
)
async def record_kana_attempt_test(
    user_id: str = Path(..., description="テストユーザーID"),
    request: KanaAttemptRequest = ...,
):
    """
    認証無しでかなレッスン結果を記録するテスト用エンドポイント。
    本番環境では使用しないでください。
    """
    try:
        logger.info(
            "[TEST] Recording kana attempt for user %s, char %s", user_id, request.char
        )
        result = await learning_service.record_learning(
            user_id=user_id,
            char=request.char,
            level=request.level,
            confidence=request.confidence,
            time=request.time,
        )
        logger.info(
            "[TEST] Successfully recorded kana attempt for user %s, char %s",
            user_id,
            request.char,
        )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "[TEST] Error recording kana attempt for user %s, char %s",
            user_id,
            request.char,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc
