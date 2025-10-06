from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from integrations.dynamodb_integration import dynamodb_sentence_composition_client

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/random")
async def get_random_sentence(
    level: int = Query(..., description="文のレベル（1-10）", ge=1, le=10)
):
    """
    指定されたレベルからランダムに1つの文を取得します
    
    Args:
        level: 文のレベル（1-10）
    
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
