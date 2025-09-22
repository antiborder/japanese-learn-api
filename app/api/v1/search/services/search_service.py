import logging
from typing import List, Dict
from fastapi import HTTPException
from integrations.dynamodb_integration import search_dynamodb_client
from schemas.search import WordSearchResult, SearchResponse, SearchRequest, Language

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        self.dynamodb_client = search_dynamodb_client

    async def search_words(self, request: SearchRequest) -> SearchResponse:
        """
        単語検索を実行します
        """
        try:
            logger.info(f"Searching words with query: '{request.query}', language: {request.language}")
            
            # 検索実行
            words_data = self.dynamodb_client.search_words(
                query=request.query,
                language=request.language.value,
                limit=request.limit,
                offset=request.offset
            )
            
            # 総数を取得
            total_count = self.dynamodb_client.get_total_count(
                query=request.query,
                language=request.language.value
            )
            
            # 結果を変換
            words = []
            for word_data in words_data:
                word = WordSearchResult(
                    id=word_data['id'],
                    name=word_data['name'],
                    hiragana=word_data['hiragana'],
                    english=word_data.get('english'),
                    vietnamese=word_data.get('vietnamese'),
                    audio_url=None  # 音声URLは別途生成が必要
                )
                words.append(word)
            
            return SearchResponse(
                words=words,
                total_count=total_count,
                query=request.query,
                language=request.language
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_words: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def search_all(self, query: str, language: Language, limit: int = 20, offset: int = 0) -> Dict:
        """
        統合検索を実行します（将来的に漢字検索、例文検索も含む）
        """
        try:
            logger.info(f"Searching all with query: '{query}', language: {language}")
            
            # 現在は単語検索のみ実装
            request = SearchRequest(
                query=query,
                language=language,
                limit=limit,
                offset=offset
            )
            
            words_result = await self.search_words(request)
            
            return {
                "words": words_result.words,
                "kanjis": [],  # 将来実装予定
                "sentences": [],  # 将来実装予定
                "total_count": words_result.total_count,
                "query": query,
                "language": language.value
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_all: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

search_service = SearchService()
