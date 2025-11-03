import logging
from typing import List, Dict
from fastapi import HTTPException
from integrations.dynamodb_integration import search_dynamodb_client
from schemas.search import WordSearchResult, KanjiSearchResult, ComponentSearchResult, SearchResponse, SearchRequest, Language

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
                    chinese=word_data.get('chinese'),
                    korean=word_data.get('korean'),
                    indonesian=word_data.get('indonesian'),
                    hindi=word_data.get('hindi'),
                    audio_url=None  # 音声URLは別途生成が必要
                )
                words.append(word)
            
            return SearchResponse(
                words=words,
                kanjis=[],  # 単語検索のみの場合は空
                components=[],  # 単語検索のみの場合は空
                total_count=total_count,
                query=request.query,
                language=request.language
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_words: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def search_kanjis(self, query: str, limit: int = 20, offset: int = 0) -> List[KanjiSearchResult]:
        """
        漢字検索を実行します（一文字の場合のみ）
        """
        try:
            logger.info(f"Searching kanjis with query: '{query}'")
            
            # 一文字でない場合は空のリストを返す
            if len(query) != 1:
                return []
            
            # 検索実行
            kanjis_data = self.dynamodb_client.search_kanjis(
                query=query,
                limit=limit,
                offset=offset
            )
            
            # 結果を変換
            kanjis = []
            for kanji_data in kanjis_data:
                kanji = KanjiSearchResult(
                    id=kanji_data['id'],
                    character=kanji_data['character'],
                    english=kanji_data.get('english'),
                    vietnamese=kanji_data.get('vietnamese'),
                    strokes=kanji_data.get('strokes'),
                    onyomi=kanji_data.get('onyomi'),
                    kunyomi=kanji_data.get('kunyomi'),
                    level=kanji_data.get('level')
                )
                kanjis.append(kanji)
            
            return kanjis
            
        except Exception as e:
            logger.error(f"Unexpected error in search_kanjis: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def search_components(self, query: str, limit: int = 20, offset: int = 0) -> List[ComponentSearchResult]:
        """
        Components検索を実行します（一文字の場合のみ）
        """
        try:
            logger.info(f"Searching components with query: '{query}'")
            
            # 一文字でない場合は空のリストを返す
            if len(query) != 1:
                return []
            
            # 検索実行
            components_data = self.dynamodb_client.search_components(
                query=query,
                limit=limit,
                offset=offset
            )
            
            # 結果を変換
            components = []
            for component_data in components_data:
                component = ComponentSearchResult(
                    id=component_data['id'],
                    character=component_data['character']
                )
                components.append(component)
            
            return components
            
        except Exception as e:
            logger.error(f"Unexpected error in search_components: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def search_all(self, query: str, language: Language, limit: int = 20, offset: int = 0) -> Dict:
        """
        統合検索を実行します（単語検索 + 漢字検索 + Components検索）
        """
        try:
            logger.info(f"Searching all with query: '{query}', language: {language}")
            
            # 単語検索
            request = SearchRequest(
                query=query,
                language=language,
                limit=limit,
                offset=offset
            )
            words_result = await self.search_words(request)
            
            # 漢字検索（一文字の場合のみ）
            kanjis = await self.search_kanjis(query, limit, offset)
            
            # Components検索（一文字の場合のみ）
            components = await self.search_components(query, limit, offset)
            
            return {
                "words": words_result.words,
                "kanjis": kanjis,
                "components": components,
                "sentences": [],  # 将来実装予定
                "total_count": words_result.total_count + len(kanjis) + len(components),
                "query": query,
                "language": language.value
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_all: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

search_service = SearchService()
