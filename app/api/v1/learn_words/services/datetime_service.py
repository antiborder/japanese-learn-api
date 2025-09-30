import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

logger = logging.getLogger(__name__)

class DateTimeService:
    def calculate_next_datetime(self, confidence: int, next_mode: str, proficiency_MJ: Decimal, proficiency_JM: Decimal, reviewable_count: int = 0) -> datetime:
        """次の学習時間を計算します
        
        Args:
            confidence: 自信度（0-3）
            next_mode: 次の学習モード（"MJ" または "JM"）
            proficiency_MJ: MJモードの習熟度（0-1）
            proficiency_JM: JMモードの習熟度（0-1）
            reviewable_count: 現在の復習可能単語数（デフォルト: 0）
            
        Returns:
            datetime: 次の学習時間
        """
        if confidence == 0:
            return datetime.now(timezone.utc) + timedelta(minutes=5)
        
        # 基本の学習間隔を計算
        if next_mode == "MJ":
            minutes = float(6 * 60 * 2**(8*float(proficiency_MJ)))
        else:  # JM
            minutes = float(6 * 60 * 2**(8*float(proficiency_JM)))
        
        # 復習可能単語数に基づくFactor補正を適用
        factor = self._calculate_factor(reviewable_count)
        minutes = minutes * factor
        
        logger.info(f"Calculated next datetime: reviewable_count={reviewable_count}, factor={factor}, minutes={minutes}")
        
        return datetime.now(timezone.utc) + timedelta(minutes=minutes)
    
    def _calculate_factor(self, reviewable_count: int) -> float:
        """復習可能単語数に基づくFactorを計算します
        
        Args:
            reviewable_count: 現在の復習可能単語数
            
        Returns:
            float: 補正Factor
        """
        if reviewable_count <= 100:
            return 1.0
        elif reviewable_count <= 500:
            return (reviewable_count + 100) / 200
        else:  # reviewable_count > 500
            return 3.0
