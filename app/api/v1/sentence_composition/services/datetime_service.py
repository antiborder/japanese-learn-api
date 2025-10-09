import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import math
from typing import Optional

logger = logging.getLogger(__name__)

class DateTimeService:
    # 定数
    BASE_HOURS = 12 # 基準となる間隔（6時間） 
    def calculate_next_datetime(self, confidence: int, proficiency: Decimal, reviewable_count: int = 0) -> datetime:
        """次の学習時間を計算します
        
        Args:
            confidence: 自信度（0-3）
            proficiency: 習熟度（0-1）
            reviewable_count: 現在の復習可能文数（デフォルト: 0）
            
        Returns:
            datetime: 次の学習時間
        """
        
        # 基本の学習間隔を計算
        minutes = float(self.BASE_INTERVAL * 2**(8*float(proficiency)))
        
        # 復習可能文数に基づくFactor補正を適用
        factor = self._calculate_factor(reviewable_count)
        minutes = minutes * factor
        
        logger.info(f"Calculated next datetime: reviewable_count={reviewable_count}, factor={factor}, minutes={minutes}")
        
        return datetime.now(timezone.utc) + timedelta(minutes=minutes)
    
    def _calculate_factor(self, reviewable_count: int) -> float:
        """復習可能文数に基づくFactorを計算します
        
        Args:
            reviewable_count: 現在の復習可能文数
            
        Returns:
            float: 補正Factor
        """
        if reviewable_count <= 100:
            return 1.0
        elif reviewable_count <= 500:
            return (reviewable_count + 100) / 200
        else:  # reviewable_count > 500
            return 3.0
    
    def calculate_interval_point(self, previous_datetime: Optional[datetime]) -> Decimal:
        """前回の学習時間との間隔から interval_point を計算します
        
        Args:
            previous_datetime: 前回の学習時間
            
        Returns:
            Decimal: interval_point（0-1の範囲）
        """
        if previous_datetime is None:
            return Decimal('0')
        
        # タイムゾーンの設定
        if previous_datetime.tzinfo is None:
            previous_datetime = previous_datetime.replace(tzinfo=timezone.utc)
        
        current_datetime = datetime.now(timezone.utc)
        previous_interval = (current_datetime - previous_datetime).total_seconds()
        
        # interval_point を計算（逆算式）
        interval_point = Decimal(str(max(0, min(1, math.log2(previous_interval/(self.BASE_HOURS * 60)) / 8))))
        
        return interval_point
