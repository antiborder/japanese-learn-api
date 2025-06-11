from fastapi import APIRouter, HTTPException
from common.schemas.learn_history import LearnHistoryRequest, LearnHistoryResponse
from integrations.dynamodb_integration import learn_history_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=LearnHistoryResponse)
async def record_learning(request: LearnHistoryRequest):
    """
    学習履歴を記録し、次の学習情報を返します。
    """
    try:
        result = await learn_history_db.record_learning(
            user_id=request.user_id,
            word_id=request.word_id,
            level=request.level,
            confidence=request.confidence,
            time=request.time
        )
        return result
    except Exception as e:
        logger.error(f"Error in record_learning endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )