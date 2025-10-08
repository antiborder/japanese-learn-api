from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, Union
import logging

from integrations.dynamodb_integration import dynamodb_sentence_composition_client
from schemas.attempt import (
    SentenceAttemptRequest, 
    SentenceAttemptResponse,
    SentenceResponse,
    NoSentenceAvailableResponse
)
from services.learning_service import LearningService
from services.next_service import NextService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/random")
async def get_random_sentence(
    level: int = Query(..., description="文のレベル（1-15）", ge=1, le=15)
):
    """
    指定されたレベルからランダムに1つの文を取得します
    
    Args:
        level: 文のレベル（1-15）
    
    Returns:
        ランダムに選ばれた文の情報
    """
    try:
        logger.info(f"Getting random sentence for level {level}")
        
        sentence = dynamodb_sentence_composition_client.get_random_sentence_by_level(level)
        
        if not sentence:
            raise HTTPException(status_code=404, detail=f"No sentences found for level {level}")
        
        logger.info(f"Successfully retrieved sentence {sentence['sentence_id']} for level {level}")
        return sentence
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting random sentence for level {level}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/users/{user_id}/attempts", response_model=SentenceAttemptResponse)
async def record_sentence_attempt(
    user_id: str = Path(..., description="ユーザーID"),
    request: SentenceAttemptRequest = ...
):
    """
    文の学習履歴を記録します
    
    Args:
        user_id: ユーザーID
        request: 学習履歴リクエスト
    
    Returns:
        学習履歴レスポンス
    """
    try:
        logger.info(f"Recording sentence attempt for user {user_id}, sentence {request.sentence_id}")
        
        learning_service = LearningService()
        
        result = await learning_service.record_learning(
            user_id=user_id,
            sentence_id=request.sentence_id,
            level=request.level,
            confidence=request.confidence,
            time=request.time
        )
        
        logger.info(f"Successfully recorded sentence attempt for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error recording sentence attempt for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/next", response_model=Union[SentenceResponse, NoSentenceAvailableResponse])
async def get_next_sentence(
    level: int = Query(..., description="文のレベル（1-15）", ge=1, le=15),
    user_id: Optional[str] = Query(None, description="ユーザーID（オプション）")
):
    """
    次に学習すべき文を取得します
    
    Args:
        level: 文のレベル（1-15）
        user_id: ユーザーID（オプション、未認証の場合はランダムに選択）
    
    Returns:
        次に学習すべき文の詳細情報
    """
    try:
        logger.info(f"Getting next sentence for user {user_id}, level {level}")
        
        next_service = NextService()
        result = await next_service.get_next_sentence(user_id, level)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"No sentences found for level {level}")
        
        # 復習可能な文がない場合
        if result.get('no_sentence_available'):
            return NoSentenceAvailableResponse(
                next_available_datetime=result.get('next_available_datetime')
            )
        
        logger.info(f"Successfully retrieved next sentence for user {user_id}, level {level}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting next sentence for user {user_id}, level {level}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
