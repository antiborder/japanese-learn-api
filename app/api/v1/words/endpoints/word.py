from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from common.schemas.word import Word, WordKanji
from common.utils.utils import convert_hiragana_to_romaji
from services.word_service import get_audio_url
from services.image_service import get_word_images
from services.ai_description_service import get_ai_description
import logging
from integrations.dynamodb_integration import dynamodb_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Word])
def read_words(skip: int = 0, limit: int = 1000):
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

@router.get("/{word_id}/kanjis", response_model=List[WordKanji])
def read_kanjis_by_word_id(word_id: int):
    """
    指定された単語IDに関連する漢字を取得します
    """
    try:
        kanjis = dynamodb_client.get_kanjis_by_word_id(word_id)
        return kanjis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading kanjis for word {word_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{word_id}/audio_url", response_model=dict)
async def fetch_word_audio(word_id: int):
    try:
        logger.info(f"Fetching audio URL for word_id: {word_id}")
        word = dynamodb_client.get_word_by_id(word_id)
        audio_url = get_audio_url(word_id, word.get('name'), word.get('hiragana'))
        return {
            "url": audio_url,
            "expires_in": 3600
        }
    except Exception as e:
        logger.error(f"Error fetching audio URL for word_id {word_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{word_id}/images", response_model=List[str])
async def fetch_word_images(word_id: int):
    """
    指定された単語の画像URLリストを取得
    
    S3に画像が存在する場合はそこから取得し、
    存在しない場合はGoogle Custom Search APIで検索してS3に保存します。
    
    Args:
        word_id: 単語ID
    
    Returns:
        署名付き画像URLの配列（最大4件、7日間有効）
    
    Raises:
        HTTPException: 単語が見つからない、またはAPI呼び出しが失敗した場合
    """
    try:
        logger.info(f"Fetching images for word_id: {word_id}")
        
        # DynamoDBから単語情報を取得
        word = dynamodb_client.get_word_by_id(word_id)
        word_name = word.get('name')
        
        if not word_name:
            raise HTTPException(status_code=404, detail="Word name not found")
        
        # 画像サービスを使用して画像URLを取得
        image_urls = get_word_images(word_id, word_name)
        
        logger.info(f"Successfully fetched {len(image_urls)} images for word_id {word_id}")
        return image_urls
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching images for word_id {word_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch images: {str(e)}")

@router.get("/{word_id}/ai-description", response_model=dict)
async def fetch_ai_description(
    word_id: int,
    lang: Optional[str] = Query(default='en', description="言語コード (en, vi, zh, hi, etc.)")
):
    """
    指定された単語のAI生成解説テキストを取得
    
    S3にキャッシュされた解説が存在する場合はそこから取得し、
    存在しない場合はGemini APIで生成してS3に保存します。
    
    Args:
        word_id: 単語ID
        lang: 言語コード（デフォルト: 'en'）
            対応言語: en (English), vi (Vietnamese), zh (Chinese), 
                     hi (Hindi), es (Spanish), fr (French), etc.
    
    Returns:
        {
            "word_id": int,
            "word_name": str,
            "language": str,
            "description": str
        }
    
    Raises:
        HTTPException: 単語が見つからない、またはAPI呼び出しが失敗した場合
    """
    try:
        logger.info(f"Fetching AI description for word_id: {word_id}, lang: {lang}")
        
        # DynamoDBから単語情報を取得
        word = dynamodb_client.get_word_by_id(word_id)
        word_name = word.get('name')
        word_meaning = word.get('meaning', '')
        
        if not word_name:
            raise HTTPException(status_code=404, detail="Word name not found")
        
        # AI解説サービスを使用して解説を取得
        description_text = get_ai_description(word_id, word_name, word_meaning, lang)
        
        logger.info(f"Successfully fetched AI description for word_id {word_id}")
        
        return {
            "word_id": word_id,
            "word_name": word_name,
            "language": lang,
            "description": description_text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching AI description for word_id {word_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch AI description: {str(e)}")