from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from common.schemas.word import Word, WordKanji, PaginatedWordsResponse, PaginationInfo
from services.word_service import get_audio_url
from services.image_service import get_word_images
from services.ai_description_service import get_ai_description
import logging
from integrations.dynamodb_integration import dynamodb_client

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=PaginatedWordsResponse)
def read_words(
    limit: int = Query(1000, ge=1, le=1000, description="1ページあたりの件数（最大: 1000）"),
    level: Optional[int] = Query(None, description="レベルフィルタ"),
    cursor: Optional[str] = Query(
        None, description="前回のレスポンスのpagination.next_cursorを渡すと続きから取得します。未指定時は先頭ページ。"
    ),
):
    """
    単語一覧を取得します（カーソルベースのページネーション対応）。
    DynamoDBから単語データを取得し、モデル形式に変換して返します。

    ページ番号（?page=N）でのランダムアクセスは提供していない。DynamoDBは
    「N件目から」を直接引けないため、それを実現しようとすると先頭から
    毎回読み直すことになり、末尾に近いページほど遅くなる（実測で最大60秒近く
    かかりAPI Gatewayの29秒制限を超えていた）。全件を順番に列挙したい場合は
    has_next=falseになるまでnext_cursorを渡し続けること。
    """
    try:
        words, next_cursor, has_next = dynamodb_client.get_words_page(limit=limit, level=level, cursor=cursor)

        return PaginatedWordsResponse(
            data=words,
            pagination=PaginationInfo(
                limit=limit,
                has_next=has_next,
                next_cursor=next_cursor,
            ),
        )
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
        audio_url = get_audio_url(word_id, word.get("name"), word.get("hiragana"))
        return {"url": audio_url, "expires_in": 3600}
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
        word_name = word.get("name")

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


@router.get("/{word_id}/ai-explanation", response_model=dict)
async def fetch_ai_description(
    word_id: int, lang: Optional[str] = Query(default="en", description="言語コード (en, vi, zh-Hans, hi, etc.)")
):
    """
    指定された単語のAI生成解説テキストを取得

    S3にキャッシュされた解説が存在する場合はそこから取得し、
    存在しない場合はGemini APIで生成してS3に保存します。

    Args:
        word_id: 単語ID
        lang: 言語コード（デフォルト: 'en'）
            対応言語: en (English), vi (Vietnamese), zh-Hans (Chinese Simplified),
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
        word_name = word.get("name")
        word_hiragana = word.get("hiragana", "")

        if not word_name:
            raise HTTPException(status_code=404, detail="Word name not found")

        # AI解説サービスを使用して解説を取得
        description_text = get_ai_description(word_id, word_name, word_hiragana, lang)

        logger.info(f"Successfully fetched AI description for word_id {word_id}")

        return {"word_id": word_id, "word_name": word_name, "language": lang, "description": description_text}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching AI description for word_id {word_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch AI description: {str(e)}")
