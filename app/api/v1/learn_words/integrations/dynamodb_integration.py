import boto3
import os
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Optional
from botocore.exceptions import ClientError
from decimal import Decimal

logger = logging.getLogger(__name__)

TIME_LIMIT = Decimal('10')

class LearnHistoryDynamoDB:
    def __init__(self):
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.table_name)

    def calculate_proficiency(self, confidence: int, time: Decimal) -> Decimal:
        """習熟度を計算します"""
        easiness_point = Decimal('0.1') + (Decimal(str(confidence))/Decimal('3')) * Decimal('0.8')
        interval_point = Decimal('0.38')
        time_point = (TIME_LIMIT - time)/TIME_LIMIT

        # 各ポイントを0-1の範囲に制限
        easiness_point = max(Decimal('0'), min(Decimal('1'), easiness_point))
        time_point = max(Decimal('0'), min(Decimal('1'), time_point))

        return Decimal('0.4') * easiness_point + Decimal('0.4') * interval_point + Decimal('0.2') * time_point

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

    async def record_learning(self, 
                            user_id: str, 
                            word_id: int, 
                            level: int,
                            confidence: int,
                            time: Decimal) -> Dict:
        """学習履歴を記録します"""
        try:
            # 現在のデータを取得
            current_data = self.get_current_learning_data(user_id, word_id)
            
            # 新しい学習モードをランダムに決定
            next_mode = random.choice(["MJ", "JM"])
            next_datetime = datetime.now() + timedelta(days=1)
            
            # 習熟度を計算
            new_proficiency = self.calculate_proficiency(confidence, time)
            
            # 現在のデータがある場合は更新、ない場合は新規作成
            if current_data:
                proficiency_MJ = new_proficiency if next_mode == "MJ" else Decimal(str(current_data.get('proficiency_MJ', '0')))
                proficiency_JM = new_proficiency if next_mode == "JM" else Decimal(str(current_data.get('proficiency_JM', '0')))
            else:
                proficiency_MJ = new_proficiency if next_mode == "MJ" else Decimal('0')
                proficiency_JM = new_proficiency if next_mode == "JM" else Decimal('0')

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
                'updated_at': datetime.now().isoformat()
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
            logger.error(f"Error recording learning data: {str(e)}")
            raise

learn_history_db = LearnHistoryDynamoDB() 