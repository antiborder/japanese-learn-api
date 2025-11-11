import logging
from typing import Optional, Union

from fastapi import APIRouter, HTTPException, Path, Query

from schemas.attempt import KanaAttemptRequest, KanaAttemptResponse
from schemas import KanaNextResponse, NoKanaAvailableResponse
from services.learning_service import LearningService
from services.next_service import NextService

logger = logging.getLogger(__name__)

router = APIRouter()
learning_service = LearningService()
next_service = NextService()


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


@router.get(
    "/next",
    response_model=Union[KanaNextResponse, NoKanaAvailableResponse],
    summary="次に学習すべきかなを取得する",
)
async def get_next_kana(
    level: int = Query(..., description="かなのレベル"),
    user_id: Optional[str] = Query(None, description="ユーザーID（任意）"),
):
    """
    次に提示すべきかなを取得します。

    level:
        レベル整数値。省略不可。
    user_id:
        ユーザーID。指定されない場合はランダムに出題します。
    """
    try:
        result = await next_service.get_next_char(level=level, user_id=user_id)
        if not result:
            raise HTTPException(status_code=404, detail="No kana found for the specified level")

        if result.get("no_char_available"):
            return NoKanaAvailableResponse(
                next_available_datetime=result.get("next_available_datetime"),
            )

        answer_char = result.get("answer_char")
        if not answer_char:
            raise HTTPException(status_code=500, detail="Invalid response from next service")

        return KanaNextResponse(answer_char=answer_char)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "Error retrieving next kana for user %s level %s", user_id, level
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc
