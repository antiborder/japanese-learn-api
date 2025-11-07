from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from common.schemas.kanji_component import Kanji, KanjiWord, PaginatedKanjisResponse, PaginationInfo
from services.kanji_service import get_kanji, get_kanjis
import logging
from pydantic import BaseModel
from integrations.dynamodb.kanji import dynamodb_kanji_client
from services.ai_description_service import get_kanji_ai_description
from schemas.ai_description_schema import KanjiAIDescriptionResponse
import math

class KanjiIdResponse(BaseModel):
    kanji_id: int

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=PaginatedKanjisResponse)
def read_kanjis_endpoint(
    page: int = Query(1, ge=1, description="ページ番号（1から開始）"),
    limit: int = Query(1000, ge=1, le=1000, description="1ページあたりの件数（最大: 1000）")
):
    """
    漢字一覧を取得します（ページネーション対応）。
    DynamoDBから漢字データを取得し、指定された形式に変換して返します。
    """
    try:
        # ページネーション計算
        skip = (page - 1) * limit
        
        # 総件数を取得
        total = dynamodb_kanji_client.count_kanjis()
        
        # DynamoDBから漢字データを取得
        kanjis = get_kanjis(skip=skip, limit=limit)
        
        # ページネーション情報を計算
        total_pages = math.ceil(total / limit) if total > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1
        
        return PaginatedKanjisResponse(
            data=kanjis,
            pagination=PaginationInfo(
                page=page,
                limit=limit,
                total=total,
                total_pages=total_pages,
                has_next=has_next,
                has_previous=has_previous
            )
        )
    except Exception as e:
        logger.error(f"Error reading kanjis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{kanji_id}", response_model=Kanji)
def read_kanji(kanji_id: int):
    try:
        kanji = get_kanji(kanji_id=kanji_id)
        if kanji is None:
            raise HTTPException(status_code=404, detail="Kanji not found")
        return kanji
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error reading kanji {kanji_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{kanji_id}/words", response_model=List[KanjiWord])
def read_words_by_kanji_id(kanji_id: int):
    """
    指定された漢字IDに関連する単語を取得します
    """
    try:
        words = dynamodb_kanji_client.get_words_by_kanji_id(kanji_id)
        return words
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading words for kanji {kanji_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{kanji_id}/components", response_model=List[dict])
def get_components_by_kanji_id(kanji_id: str):
    try:
        return dynamodb_kanji_client.get_components_by_kanji_id(str(kanji_id))
    except Exception as e:
        logger.error(f"Error getting components for kanji {kanji_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{kanji_id}/ai-explanation", response_model=KanjiAIDescriptionResponse)
async def fetch_kanji_ai_description(
    kanji_id: int,
    lang: Optional[str] = Query(default='en', description="言語コード (en, vi, zh-Hans, hi, etc.)")
):
    """
    指定された漢字のAI生成解説テキストを取得
    
    S3にキャッシュされた解説が存在する場合はそこから取得し、
    存在しない場合はGemini APIで生成してS3に保存します。
    
    Args:
        kanji_id: 漢字ID
        lang: 言語コード（デフォルト: 'en'）
            対応言語: en (English), vi (Vietnamese), zh-Hans (Chinese Simplified), 
                     hi (Hindi), es (Spanish), fr (French), etc.
    
    Returns:
        {
            "kanji_id": int,
            "kanji_character": str,
            "language": str,
            "description": str
        }
    
    Raises:
        HTTPException: 漢字が見つからない、またはAPI呼び出しが失敗した場合
    """
    try:
        logger.info(f"Fetching AI description for kanji_id: {kanji_id}, lang: {lang}")
        
        # DynamoDBから漢字情報を取得
        kanji = get_kanji(kanji_id=kanji_id)
        if kanji is None:
            raise HTTPException(status_code=404, detail="Kanji not found")
        
        # 辞書の場合は'character'キーでアクセス、オブジェクトの場合は.characterでアクセス
        if isinstance(kanji, dict):
            kanji_character = kanji.get('character')
        else:
            kanji_character = kanji.character
        
        if not kanji_character:
            raise HTTPException(status_code=404, detail="Kanji character not found")
        
        # AI解説サービスを使用して解説を取得
        description_text = get_kanji_ai_description(kanji_id, kanji_character, lang)
        
        logger.info(f"Successfully fetched AI description for kanji_id {kanji_id}")
        
        return KanjiAIDescriptionResponse(
            kanji_id=kanji_id,
            kanji_character=kanji_character,
            language=lang,
            description=description_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching AI description for kanji_id {kanji_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch AI description: {str(e)}")