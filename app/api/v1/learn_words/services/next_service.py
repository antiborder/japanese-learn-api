import logging
import random
from datetime import datetime, timezone
from typing import Dict, Optional, List, Union
from fastapi import HTTPException
from integrations.dynamodb.next import NextDynamoDB
from services.word_selector import WordSelector
from services.review_logic import ReviewLogic

logger = logging.getLogger(__name__)

class NextService:
    def __init__(self):
        self.next_db = NextDynamoDB()
        self.word_selector = WordSelector()
        self.review_logic = ReviewLogic()

    async def get_random_word(self, level: int) -> Optional[Dict]:
        """指定されたレベルからランダムに単語IDとモードを取得します"""
        try:
            # ①単語リストの取得とレベルでのフィルタリング
            level_words = await self.next_db._get_level_words(level)
            if not level_words:
                return None

            # ②ランダムに単語を選択
            result = self.word_selector.select_random_word(level_words)
            logger.info(f"Successfully retrieved random word for level {level}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error getting random word for level {level}: {str(e)}", exc_info=True)
            raise

    async def get_next_word(self, user_id: str, level: Union[int, str]) -> Optional[Dict]:
        """次に学習すべき単語を取得します"""
        try:
            # REVIEW_ALLの場合の特別処理
            if level == "REVIEW_ALL":
                return await self._get_next_word_review_all(user_id)
            
            # 通常のレベル指定の場合
            level_int = int(level)
            
            # ①単語リストの取得とレベルでのフィルタリング
            level_words = await self.next_db._get_level_words(level_int)
            if not level_words:
                return None
            
            # ③ユーザーの学習履歴の取得とレベルでのフィルタリング（user-level-index GSIを使用）
            user_level_words = await self.next_db._get_user_words_by_level(user_id, level_int)
            # word_selector.select_next_wordの引数としてuser_wordsが必要（後方互換性のため）
            # 実際にはuser_level_wordsが提供されれば、select_next_word内でuser_wordsは使用されない
            user_words = await self.next_db._get_user_words(user_id)
            
            # ④単語選定方法の決定
            # GSIで取得したuser_level_wordsを直接渡すことで、DynamoDB側でフィルタリング済みのデータを使用
            return self.word_selector.select_next_word(level_words, user_words, user_id, level_int, user_level_words)
        except Exception as e:
            logger.error(f"Error getting next word for user {user_id}, level {level}: {str(e)}", exc_info=True)
            raise

    async def _get_next_word_review_all(self, user_id: str) -> Optional[Dict]:
        """全レベルから復習可能な単語を取得します（next_datetimeが最も古いものを選択）"""
        try:
            # ユーザーの学習履歴を全て取得
            user_words = await self.next_db._get_user_words(user_id)
            if not user_words:
                logger.info(f"No learning history found for user {user_id}")
                return None
            
            return self.review_logic.get_review_all_word(user_words)
        except Exception as e:
            logger.error(f"Error getting all-review word for user {user_id}: {str(e)}", exc_info=True)
            raise

    async def get_other_words(self, level: Union[int, str], exclude_id: int) -> List[int]:
        """指定されたレベルで、除外ID以外の単語を3つ取得します"""
        try:
            # ALL_REVIEWの場合の特別処理
            if level == "REVIEW_ALL":
                return await self._get_other_words_review_all(exclude_id)
            
            # 通常のレベル指定の場合
            level_int = int(level)
            
            level_words = await self.next_db._get_level_words(level_int)
            if not level_words:
                logger.info(f"No words found in the database")
                return []
            
            # レベルでフィルタリングし、除外IDを除く
            filtered_items = [
                item for item in level_words 
                if int(item['SK']) != exclude_id
            ]
            if len(filtered_items) < 3:
                logger.info(f"Not enough words found for level {level_int} excluding word {exclude_id}")
                return []
            
            # ランダムに3つ選択
            selected_items = random.sample(filtered_items, 3)
            # word_idのリストを返す
            word_ids = [int(item['SK']) for item in selected_items]
            logger.info(f"Successfully retrieved 3 other words for level {level_int}, excluding word {exclude_id}")
            return word_ids
        except Exception as e:
            logger.error(f"Error getting other words for level {level}, excluding word {exclude_id}: {str(e)}", exc_info=True)
            raise

    async def _get_other_words_review_all(self, exclude_id: int) -> List[int]:
        """全レベルから除外ID以外の単語を3つ取得します"""
        try:
            # 全単語を取得
            items = await self.next_db._get_all_words()
            if not items:
                logger.info(f"No words found in the database")
                return []
            
            # 除外IDを除く
            filtered_items = [
                item for item in items 
                if int(item['SK']) != exclude_id
            ]
            if len(filtered_items) < 3:
                logger.info(f"Not enough words found excluding word {exclude_id}")
                return []
            
            # ランダムに3つ選択
            selected_items = random.sample(filtered_items, 3)
            # word_idのリストを返す
            word_ids = [int(item['SK']) for item in selected_items]
            logger.info(f"Successfully retrieved 3 other words from all levels, excluding word {exclude_id}")
            return word_ids
        except Exception as e:
            logger.error(f"Error getting other words from all levels, excluding word {exclude_id}: {str(e)}", exc_info=True)
            raise

    async def get_word_detail(self, word_id: int) -> dict:
        """単語詳細を取得します"""
        return await self.next_db.get_word_detail(word_id)
