import logging
import random
from typing import Dict, List, Optional, Union
from datetime import datetime, timezone

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
    def select_review_word(user_level_words: List[Dict]) -> Optional[Dict]:
        """復習単語を選択します"""
        if not user_level_words:
            return None
        
        # 復習可能な単語をフィルタリング
        reviewable_words = []
        for word in user_level_words:
            if WordSelector._is_reviewable(word):
                reviewable_words.append(word)
        
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
                        user_id: str, level: Union[int, str]) -> Optional[Dict]:
        """次に学習すべき単語を選択します"""
        level_int = int(level) if isinstance(level, str) else level
        user_level_words = [item for item in user_words if item.get('level') == level_int]
        
        # ④単語選定方法の決定
        ratio = len(user_level_words) / len(level_words)
        if random.random() > ratio:
            # random_selection: 新しい単語を選択
            new_word_result = WordSelector.select_new_word(level_words, user_level_words)
            if new_word_result:
                logger.info(f"Successfully retrieved new word for user {user_id}, level {level_int}: {new_word_result}")
                return new_word_result
        
        # review_selection: 復習単語を選択
        review_word_result = WordSelector.select_review_word(user_level_words)
        if review_word_result:
            logger.info(f"Successfully retrieved review word for user {user_id}, level {level_int}: {review_word_result}")
            return review_word_result
        
        # 復習可能な単語がない場合は、次に利用可能になる時刻を計算
        next_available_dt = WordSelector._get_next_available_time(user_level_words)
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
    
    @staticmethod
    def _is_reviewable(word: dict) -> bool:
        """単語が復習可能かどうかをチェックします"""
        if 'next_datetime' not in word:
            return False
        
        try:
            next_dt = datetime.fromisoformat(word['next_datetime'])
            if next_dt.tzinfo is None:
                next_dt = next_dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            return next_dt <= now
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid next_datetime format for word {word.get('word_id')}: {e}")
            return False
    
    @staticmethod
    def _get_next_available_time(user_words: list) -> Optional[datetime]:
        """次に利用可能になる時刻を取得します"""
        if not user_words:
            return None
        
        try:
            next_available_word = min(user_words, key=lambda x: x['next_datetime'])
            next_dt = datetime.fromisoformat(next_available_word['next_datetime'])
            if next_dt.tzinfo is None:
                next_dt = next_dt.replace(tzinfo=timezone.utc)
            return next_dt
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid next_datetime format for next available word: {e}")
            return None 