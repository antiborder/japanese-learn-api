import logging
from datetime import datetime
from typing import Dict, Optional
from decimal import Decimal
from .datetime_service import DateTimeService

logger = logging.getLogger(__name__)

TIME_LIMIT = Decimal('10')

class ProficiencyService:
    def __init__(self):
        self.datetime_service = DateTimeService()
    
    def calculate_proficiency(self, confidence: int, time: Decimal, current_data: Optional[Dict] = None) -> Decimal:
        """習熟度を計算します"""
        easiness_point = Decimal('0.1') + (Decimal(str(confidence))/Decimal('3')) * Decimal('0.8')
        
        # 前回の学習時間との差を計算
        if current_data and 'updated_at' in current_data:
            previous_datetime = datetime.fromisoformat(current_data['updated_at'])
            interval_point = self.datetime_service.calculate_interval_point(previous_datetime)
        else:
            interval_point = Decimal('0')

        time_point = (TIME_LIMIT - time)/TIME_LIMIT

        # 各ポイントを0-1の範囲に制限
        easiness_point = max(Decimal('0'), min(Decimal('1'), easiness_point))
        time_point = max(Decimal('0'), min(Decimal('1'), time_point))

        return Decimal('0.4') * easiness_point + Decimal('0.4') * interval_point + Decimal('0.2') * time_point
