import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from .datetime_utils import DateTimeUtils

logger = logging.getLogger(__name__)

class ReviewLogic:
    @staticmethod
    def get_reviewable_words(user_words: List[Dict]) -> List[Dict]:
        """復習可能な単語を取得します"""
        reviewable_words = []
        for word in user_words:
            if DateTimeUtils.is_reviewable(word):
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
            next_available_dt = DateTimeUtils.get_next_available_time(user_words)
            if next_available_dt:
                result = {
                    'no_word_available': True,
                    'next_available_datetime': next_available_dt
                }
                logger.info(f"No reviewable words available in all levels. Next available at: {next_available_dt}")
                return result
        
        return None 