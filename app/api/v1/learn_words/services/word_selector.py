import logging
import random
from typing import Dict, List, Optional, Set, Union
from datetime import datetime, timezone
from .datetime_utils import DateTimeUtils

logger = logging.getLogger(__name__)

class WordSelector:
    @staticmethod
    def select_new_word(level_words: List[Dict], user_words: List[Dict]) -> Optional[Dict]:
        """新しい単語を選択します"""
        # ユーザーが学習済みの単語IDを取得
        user_learned_ids = [int(w['word_id']) for w in user_words]
        
        # 新しい単語（学習済みでない単語）をフィルタリング
        new_words = [
            word for word in level_words 
            if int(word['SK']) not in user_learned_ids
        ]
        
        if not new_words:
            return None
        
        # ランダムに選択
        selected_item = random.choice(new_words)
        return {
            'answer_word_id': int(selected_item['SK']),
            'mode': random.choice(["MJ", "JM"])
        }
    
    @staticmethod
    def select_review_word(
        user_level_words: List[Dict],
        existing_word_ids: Optional[Set[int]] = None,
    ) -> Optional[Dict]:
        """Select a review word.

        If existing_word_ids is provided (SKs from the already-loaded level word list),
        history rows whose word_id is not in that set are skipped so the next earliest
        next_datetime is used when the WORD row was removed from the catalog.
        """
        if not user_level_words:
            return None
        
        # 復習可能な単語をフィルタリング
        reviewable_words = []
        for word in user_level_words:
            if DateTimeUtils.is_reviewable(word):
                reviewable_words.append(word)

        if existing_word_ids is not None:
            before = len(reviewable_words)
            reviewable_words = [
                w for w in reviewable_words
                if int(w["word_id"]) in existing_word_ids
            ]
            if before and len(reviewable_words) < before:
                logger.warning(
                    "Skipped %d review candidate(s) with no WORD row for this level",
                    before - len(reviewable_words),
                )
        
        if not reviewable_words:
            return None
        
        # next_datetimeが最も古いものを選択
        answer_word = min(reviewable_words, key=lambda x: x['next_datetime'])
        return {
            'answer_word_id': answer_word['word_id'],
            'mode': answer_word['next_mode']
        }
    
    @staticmethod
    def select_random_word(level_words: List[Dict]) -> Optional[Dict]:
        """ランダムに単語を選択します"""
        if not level_words:
            return None
        
        selected_item = random.choice(level_words)
        return {
            'answer_word_id': int(selected_item['SK']),
            'mode': random.choice(["MJ", "JM"])
        }
    
    @staticmethod
    def select_next_word(level_words: List[Dict], user_words: List[Dict], 
                        user_id: str, level: Union[int, str], 
                        user_level_words: Optional[List[Dict]] = None) -> Optional[Dict]:
        """次に学習すべき単語を選択します"""
        level_int = int(level) if isinstance(level, str) else level
        # user_level_wordsが提供されていない場合は、user_wordsからフィルタリング
        if user_level_words is None:
            user_level_words = [item for item in user_words if item.get('level') == level_int]
        
        # ④単語選定方法の決定
        ratio = len(user_level_words) / len(level_words) if level_words else 0
        if random.random() > ratio:
            # random_selection: 新しい単語を選択
            new_word_result = WordSelector.select_new_word(level_words, user_level_words)
            if new_word_result:
                logger.info(f"Successfully retrieved new word for user {user_id}, level {level_int}: {new_word_result}")
                return new_word_result
        
        # review_selection: only words present in the already-fetched level word list
        level_word_ids = {int(w["SK"]) for w in level_words}
        review_word_result = WordSelector.select_review_word(
            user_level_words, existing_word_ids=level_word_ids
        )
        if review_word_result:
            logger.info(f"Successfully retrieved review word for user {user_id}, level {level_int}: {review_word_result}")
            return review_word_result
        
        # 復習単語がない場合、改めて新しい単語を試す
        new_word_result = WordSelector.select_new_word(level_words, user_level_words)
        if new_word_result:
            logger.info(f"No review available, retrieved new word for user {user_id}, level {level_int}: {new_word_result}")
            return new_word_result
        
        # 復習可能な単語がない場合は、次に利用可能になる時刻を計算
        next_available_dt = DateTimeUtils.get_next_available_time(user_level_words)
        if next_available_dt:
            result = {
                'no_word_available': True,
                'next_available_datetime': next_available_dt
            }
            logger.info(f"No reviewable words available for user {user_id}, level {level_int}. Next available at: {next_available_dt}")
            return result
        
        # ユーザーの学習履歴に単語がない場合は、ランダムに選択
        random_result = WordSelector.select_random_word(level_words)
        logger.info(f"Successfully retrieved random word for user {user_id}, level {level_int}: {random_result}")
        return random_result 