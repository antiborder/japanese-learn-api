from fastapi import APIRouter, HTTPException
from common.schemas.learn_history import LearnHistoryRequest, LearnHistoryResponse, NextWordRequest, NextWordResponse
from integrations.dynamodb_integration import learn_history_db
import logging
from pydantic import BaseModel, Field
from typing import List

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

@router.post("/next", response_model=NextWordResponse)
async def get_next_word(request: NextWordRequest):
    """
    次に学習すべき単語を取得します。
    """
    try:
        result = await learn_history_db.get_next_word(
            user_id=request.user_id,
            level=request.level
        )
        
        if result is None:
            raise HTTPException(
                status_code=404,
                detail="No words found for the specified level"
            )
            
        return NextWordResponse(
            answer_word_id=int(result['answer_word_id']),
            mode=result['mode']
        )
    except Exception as e:
        logger.error(f"Error in get_next_word endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

class OtherWordsRequest(BaseModel):
    level: int = Field(..., description="取得する単語のレベル")
    answer_word_id: int = Field(..., description="正解の単語ID（このIDは選択肢から除外されます）")

@router.post("/other_words", response_model=List[int])
async def get_other_words(request: OtherWordsRequest) -> List[int]:
    """指定されたレベルで、正解の単語ID以外の単語を3つ取得します。
    
    このエンドポイントは、クイズの選択肢として使用する単語を取得します。
    指定されたレベルに属し、正解の単語IDと異なる単語からランダムに3つを選択します。
    
    Args:
        request: OtherWordsRequest
            - level: 取得する単語のレベル
            - answer_word_id: 正解の単語ID（このIDは選択肢から除外されます）
    
    Returns:
        List[int]: 3つの単語IDのリスト（選択肢として使用する単語）
    
    Raises:
        HTTPException: 404 - 条件に合致する単語が3つ未満の場合
        HTTPException: 500 - その他のエラー
    """
    try:
        word_ids = await learn_history_db.get_other_words(request.level, request.answer_word_id)
        if not word_ids:
            raise HTTPException(status_code=404, detail="Not enough words found for the specified level")
        return word_ids
    except Exception as e:
        logger.error(f"Error getting other words: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))