import logging
from datetime import datetime, timezone
from typing import Optional, Sequence, Mapping, Any

logger = logging.getLogger(__name__)


class DateTimeUtils:
    @staticmethod
    def parse_datetime_safe(dt_str: str) -> Optional[datetime]:
        """ISO形式の文字列をdatetimeに変換します。"""
        if not dt_str:
            return None
        try:
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (TypeError, ValueError) as exc:
            logger.warning("Invalid datetime format detected: %s error=%s", dt_str, exc)
            return None

    @staticmethod
    def is_reviewable(item: Mapping[str, Any]) -> bool:
        """復習可能かどうかを判定します。"""
        next_dt_raw = item.get("next_datetime")
        next_dt = DateTimeUtils.parse_datetime_safe(next_dt_raw)
        if next_dt is None:
            return False
        now = datetime.now(timezone.utc)
        return next_dt <= now

    @staticmethod
    def get_next_available_time(items: Sequence[Mapping[str, Any]]) -> Optional[datetime]:
        """次に復習可能になる時刻を取得します。"""
        if not items:
            return None
        try:
            next_available = min(
                (DateTimeUtils.parse_datetime_safe(item.get("next_datetime")) for item in items),
                default=None,
                key=lambda value: value or datetime.max.replace(tzinfo=timezone.utc),
            )
            return next_available
        except Exception as exc:
            logger.warning("Failed to compute next available time: %s", exc)
            return None

