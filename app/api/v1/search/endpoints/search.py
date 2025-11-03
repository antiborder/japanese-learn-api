from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from services.search_service import search_service
from schemas.search import SearchRequest, Language, SearchResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/words", response_model=SearchResponse)
async def search_words(
    q: str = Query(..., description="検索クエリ"),
    lang: str = Query(..., description="言語コード (en, vi, zh-Hans, ko, id, hi)"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="取得件数"),
    offset: Optional[int] = Query(0, ge=0, description="オフセット")
):
    """
    単語検索エンドポイント
    """
    try:
        # 言語コードの検証
        try:
            language = Language(lang)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid language code. Must be 'en', 'vi', 'zh-Hans', 'ko', 'id', or 'hi'"
            )
        
        # リクエスト作成
        request = SearchRequest(
            query=q,
            language=language,
            limit=limit,
            offset=offset
        )
        
        # 検索実行
        result = await search_service.search_words(request)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in search_words endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/all")
async def search_all(
    q: str = Query(..., description="検索クエリ"),
    lang: str = Query(..., description="言語コード (en, vi, zh-Hans, ko, id, hi)"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="取得件数"),
    offset: Optional[int] = Query(0, ge=0, description="オフセット")
):
    """
    統合検索エンドポイント（単語、漢字、例文を一括検索）
    """
    try:
        # 言語コードの検証
        try:
            language = Language(lang)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid language code. Must be 'en', 'vi', 'zh-Hans', 'ko', 'id', or 'hi'"
            )
        
        # 統合検索実行
        result = await search_service.search_all(
            query=q,
            language=language,
            limit=limit,
            offset=offset
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in search_all endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
