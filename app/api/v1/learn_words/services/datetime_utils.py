import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

class DateTimeUtils:
    @staticmethod
    def parse_datetime_safe(dt_str: str) -> Optional[datetime]:
        """安全な日時解析を行います"""
        try:
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid datetime format: {dt_str}, error: {e}")
            return None
    
    @staticmethod
    def is_reviewable(word: dict) -> bool:
        """単語が復習可能かどうかをチェックします"""
        if 'next_datetime' not in word:
            return False
        
        next_dt = DateTimeUtils.parse_datetime_safe(word['next_datetime'])
        if next_dt is None:
            return False
        
        now = datetime.now(timezone.utc)
        return next_dt <= now
    
    @staticmethod
    def get_next_available_time(user_words: list) -> Optional[datetime]:
        """次に利用可能になる時刻を取得します"""
        if not user_words:
            return None
        
        try:
            # next_datetimeが最も古い単語を取得
            next_available_word = min(user_words, key=lambda x: x['next_datetime'])
            return DateTimeUtils.parse_datetime_safe(next_available_word['next_datetime'])
        except (KeyError, ValueError) as e:
            logger.warning(f"Error getting next available time: {e}")
            return None 