
from fastapi import APIRouter, HTTPException
from typing import List
from common.schemas.sentence import Sentence
from integrations.dynamodb_integration import dynamodb_sentence_client
from services.sentence_audio_service import get_sentence_audio_url
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Sentence])
def read_sentences(skip: int = 0, limit: int = 1000):
    """
    文一覧を取得します。
    DynamoDBから文データを取得し、指定された形式に変換して返します。
    """
    try:
        # DynamoDBから文データを取得
        sentences = dynamodb_sentence_client.get_sentences(skip=skip, limit=limit)
        return sentences
    except Exception as e:
        logger.error(f"Error reading sentences: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{sentence_id}", response_model=Sentence)
def read_sentence(sentence_id: int):
    """
    指定されたIDの文を取得します。
    """
    try:
        sentence = dynamodb_sentence_client.get_sentence_by_id(sentence_id)
        return sentence
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading sentence {sentence_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{sentence_id}/audio_url", response_model=dict)
async def fetch_sentence_audio(sentence_id: int):
    """
    例文の音声URLを取得します
    """
    try:
        logger.info(f"Fetching audio URL for sentence_id: {sentence_id}")
        
        # 例文データを取得
        sentence = dynamodb_sentence_client.get_sentence_by_id(sentence_id)
        
        # 音声URLを取得
        audio_url = get_sentence_audio_url(
            sentence_id, 
            sentence.get('japanese'), 
            sentence.get('hurigana', '')
        )
        
        return {
            "url": audio_url,
            "expires_in": 3600
        }
    except Exception as e:
        logger.error(f"Error fetching audio URL for sentence_id {sentence_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
