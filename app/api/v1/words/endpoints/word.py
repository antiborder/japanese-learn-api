from fastapi import APIRouter, HTTPException
from typing import List
from common.schemas.word import Word
from common.utils.utils import convert_hiragana_to_romaji
from services.word_service import get_audio_url
import logging
from integrations.dynamodb_integration import dynamodb_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Word])
def read_words(skip: int = 0, limit: int = 100):
    """
    単語一覧を取得します。
    DynamoDBから単語データを取得し、MySQLのモデル形式に変換して返します。
    """
    try:
        # DynamoDBから単語データを取得
        words = dynamodb_client.get_words(skip=skip, limit=limit)
        return words
    except Exception as e:
        logger.error(f"Error reading words: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{word_id}", response_model=Word)
def read_word(word_id: int):
    try:
        word = dynamodb_client.get_word_by_id(word_id)
        return word
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading word {word_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{word_id}/audio_url", response_model=dict)
async def fetch_word_audio(word_id: int):
    try:
        logger.info(f"Fetching audio URL for word_id: {word_id}")
        word = dynamodb_client.get_word_by_id(word_id)
        audio_url = get_audio_url(word_id, word.get('hiragana'))
        return {
            "url": audio_url,
            "expires_in": 3600
        }
    except Exception as e:
        logger.error(f"Error fetching audio URL for word_id {word_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))