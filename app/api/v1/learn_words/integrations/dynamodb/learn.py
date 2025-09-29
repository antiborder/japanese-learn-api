import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from botocore.exceptions import ClientError
from decimal import Decimal
from fastapi import HTTPException
from .base import DynamoDBBase
from services.proficiency_service import ProficiencyService
from services.mode_service import ModeService
from services.datetime_service import DateTimeService

logger = logging.getLogger(__name__)

class LearnDynamoDB(DynamoDBBase):
    def __init__(self):
        super().__init__()
        self.proficiency_service = ProficiencyService()
        self.mode_service = ModeService()
        self.datetime_service = DateTimeService()

    def calculate_proficiency(self, confidence: int, time: Decimal, current_data: Optional[Dict] = None) -> Decimal:
        """習熟度を計算します"""
        return self.proficiency_service.calculate_proficiency(confidence, time, current_data)

    def determine_next_mode(self, proficiency_MJ: Decimal, proficiency_JM: Decimal) -> str:
        """次の学習モードを決定します"""
        return self.mode_service.determine_next_mode(proficiency_MJ, proficiency_JM)

    def calculate_next_datetime(self, confidence: int, next_mode: str, proficiency_MJ: Decimal, proficiency_JM: Decimal) -> datetime:
        """次の学習時間を計算します"""
        return self.datetime_service.calculate_next_datetime(confidence, next_mode, proficiency_MJ, proficiency_JM)

    def get_current_learning_data(self, user_id: str, word_id: int) -> Optional[Dict]:
        """現在の学習データを取得します"""
        try:
            response = self.table.get_item(
                Key={
                    'PK': f"USER#{user_id}",
                    'SK': f"WORD#{word_id}"
                }
            )
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting learning data: {str(e)}")
            return None

    async def save_learning_data(self, 
                                user_id: str, 
                                word_id: int, 
                                level: int,
                                proficiency_MJ: Decimal,
                                proficiency_JM: Decimal,
                                next_mode: str,
                                next_datetime: datetime) -> Dict:
        """学習データをDynamoDBに保存します（DB操作のみ）"""
        try:
            # DynamoDBに保存するアイテムを作成
            item = {
                'PK': f"USER#{user_id}",
                'SK': f"WORD#{word_id}",
                'user_id': user_id,
                'word_id': word_id,
                'level': level,
                'proficiency_MJ': proficiency_MJ,
                'proficiency_JM': proficiency_JM,
                'next_mode': next_mode,
                'next_datetime': next_datetime.isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # DynamoDBに保存
            self.table.put_item(Item=item)
            
            return {
                'user_id': user_id,
                'word_id': word_id,
                'level': level,
                'proficiency_MJ': proficiency_MJ,
                'proficiency_JM': proficiency_JM,
                'next_mode': next_mode,
                'next_datetime': next_datetime
            }
            
        except Exception as e:
            logger.error(f"Error saving learning data: {str(e)}")
            raise 