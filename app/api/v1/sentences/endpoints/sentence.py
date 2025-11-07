
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from common.schemas.sentence import Sentence, SentenceGrammarDescription, PaginatedSentencesResponse, PaginationInfo
from integrations.dynamodb_integration import dynamodb_sentence_client
from services.sentence_audio_service import get_sentence_audio_url
from services.ai_grammar_service import get_sentence_grammar_description
import logging
import math

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=PaginatedSentencesResponse)
def read_sentences(
    page: int = Query(1, ge=1, description="ページ番号（1から開始）"),
    limit: int = Query(1000, ge=1, le=1000, description="1ページあたりの件数（最大: 1000）")
):
    """
    文一覧を取得します（ページネーション対応）。
    DynamoDBから文データを取得し、指定された形式に変換して返します。
    """
    try:
        # ページネーション計算
        skip = (page - 1) * limit
        
        # 総件数を取得
        total = dynamodb_sentence_client.count_sentences()
        
        # DynamoDBから文データを取得
        sentences = dynamodb_sentence_client.get_sentences(skip=skip, limit=limit)
        
        # ページネーション情報を計算
        total_pages = math.ceil(total / limit) if total > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1
        
        return PaginatedSentencesResponse(
            data=sentences,
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

@router.get("/{sentence_id}/ai-explanation", response_model=SentenceGrammarDescription)
async def fetch_ai_grammar_description(
    sentence_id: int,
    lang: Optional[str] = Query(default='en', description="言語コード (en, vi, zh-Hans, hi, etc.)")
):
    """
    指定された例文のAI生成文法解説テキストを取得
    
    S3にキャッシュされた解説が存在する場合はそこから取得し、
    存在しない場合はGemini APIで生成してS3に保存します。
    
    Args:
        sentence_id: 例文ID
        lang: 言語コード（デフォルト: 'en'）
            対応言語: en (English), vi (Vietnamese), zh-Hans (Chinese Simplified), 
                     hi (Hindi), es (Spanish), fr (French), etc.
    
    Returns:
        {
            "sentence_id": int,
            "sentence_text": str,
            "jlpt_level": str,
            "language": str,
            "description": str
        }
    
    Raises:
        HTTPException: 例文が見つからない、またはAPI呼び出しが失敗した場合
    """
    try:
        logger.info(f"Fetching AI grammar description for sentence_id: {sentence_id}, lang: {lang}")
        
        # DynamoDBから例文情報を取得
        sentence = dynamodb_sentence_client.get_sentence_by_id(sentence_id)
        sentence_text = sentence.get('japanese')
        level = sentence.get('level', 1)
        
        if not sentence_text:
            raise HTTPException(status_code=404, detail="Sentence text not found")
        
        # AI文法解説サービスを使用して解説を取得
        description_text = get_sentence_grammar_description(sentence_id, sentence_text, level, lang)
        
        # レベルからJLPT級を決定
        if 1 <= level <= 3:
            jlpt_level = "N5"
        elif 4 <= level <= 6:
            jlpt_level = "N4"
        elif 7 <= level <= 9:
            jlpt_level = "N3"
        elif 10 <= level <= 12:
            jlpt_level = "N2"
        elif 13 <= level <= 15:
            jlpt_level = "N1"
        else:
            jlpt_level = "N5"
        
        logger.info(f"Successfully fetched AI grammar description for sentence_id {sentence_id}")
        
        return {
            "sentence_id": sentence_id,
            "sentence_text": sentence_text,
            "jlpt_level": jlpt_level,
            "language": lang,
            "description": description_text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching AI grammar description for sentence_id {sentence_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch AI grammar description: {str(e)}")
