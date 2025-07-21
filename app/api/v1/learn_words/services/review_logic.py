import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ReviewLogic:
    @staticmethod
    def get_reviewable_words(user_words: List[Dict]) -> List[Dict]:
        """復習可能な単語を取得します"""
        reviewable_words = []
        for word in user_words:
            if ReviewLogic._is_reviewable(word):
                reviewable_words.append(word)
        return reviewable_words
    
    @staticmethod
    def get_review_all_word(user_words: List[Dict]) -> Optional[Dict]:
        """全レベルから復習可能な単語を取得します（next_datetimeが最も古いものを選択）"""
        if not user_words:
            logger.info("No learning history found")
            return None
        
        # 復習可能な単語をフィルタリング
        reviewable_words = ReviewLogic.get_reviewable_words(user_words)
        
        if reviewable_words:
            # 復習可能な単語がある場合は、next_datetimeが最も古いものを選択
            answer_word = min(reviewable_words, key=lambda x: x['next_datetime'])
            result = {
                'answer_word_id': answer_word['word_id'],
                'mode': answer_word['next_mode']
            }
            logger.info(f"Successfully retrieved all-review word: {result}")
            return result
        else:
            # 復習可能な単語がない場合は、次に利用可能になる時刻を計算
            next_available_dt = ReviewLogic._get_next_available_time(user_words)
            if next_available_dt:
                result = {
                    'no_word_available': True,
                    'next_available_datetime': next_available_dt
                }
                logger.info(f"No reviewable words available in all levels. Next available at: {next_available_dt}")
                return result
        
        return None
    
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