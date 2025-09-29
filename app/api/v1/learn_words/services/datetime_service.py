import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

logger = logging.getLogger(__name__)

class DateTimeService:
    def calculate_next_datetime(self, confidence: int, next_mode: str, proficiency_MJ: Decimal, proficiency_JM: Decimal) -> datetime:
        """次の学習時間を計算します
        
        Args:
            confidence: 自信度（0-3）
            next_mode: 次の学習モード（"MJ" または "JM"）
            proficiency_MJ: MJモードの習熟度（0-1）
            proficiency_JM: JMモードの習熟度（0-1）
            
        Returns:
            datetime: 次の学習時間
        """
        if confidence == 0:
            return datetime.now(timezone.utc) + timedelta(minutes=5)
        
        if next_mode == "MJ":
            minutes = float(6 * 60 * 2**(8*float(proficiency_MJ)))
        else:  # JM
            minutes = float(6 * 60 * 2**(8*float(proficiency_JM)))
        
        return datetime.now(timezone.utc) + timedelta(minutes=minutes)
