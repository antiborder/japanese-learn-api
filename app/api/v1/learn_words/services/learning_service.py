import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from decimal import Decimal
from integrations.dynamodb.learn import LearnDynamoDB

logger = logging.getLogger(__name__)

class LearningService:
    def __init__(self):
        self.learn_db = LearnDynamoDB()
        self.proficiency_service = self.learn_db.proficiency_service
        self.mode_service = self.learn_db.mode_service
        self.datetime_service = self.learn_db.datetime_service

    async def record_learning(self, 
                            user_id: str, 
                            word_id: int, 
                            level: int,
                            confidence: int,
                            time: Decimal) -> Dict:
        """学習履歴を記録します（ビジネスロジック）"""
        try:
            # ユーザーIDがない場合は記録をスキップ
            if not user_id:
                logger.info("User ID is null or empty. Skipping DynamoDB record.")
                return {
                    'user_id': user_id,
                    'word_id': word_id,
                    'level': level,
                    'proficiency_MJ': Decimal('0'),
                    'proficiency_JM': Decimal('0'),
                    'next_mode': "MJ",  # デフォルトモード
                    'next_datetime': datetime.now(timezone.utc) + timedelta(minutes=5)  # デフォルトの次回学習時間
                }

            # 現在のデータを取得
            current_data = self.learn_db.get_current_learning_data(user_id, word_id)
                        
            # 現在のデータがある場合は更新、ない場合は新規作成
            if current_data:
                proficiency_MJ = Decimal(str(current_data.get('proficiency_MJ', '0')))
                proficiency_JM = Decimal(str(current_data.get('proficiency_JM', '0')))
            else:
                proficiency_MJ = Decimal('0')
                proficiency_JM = Decimal('0')
            
            # 次の学習モードを決定
            next_mode = self.mode_service.determine_next_mode(proficiency_MJ, proficiency_JM)

            # 習熟度を計算
            new_proficiency = self.proficiency_service.calculate_proficiency(confidence, time, current_data)            
            
            # 新しい習熟度を更新
            if next_mode == "MJ":
                proficiency_MJ = new_proficiency
            else:
                proficiency_JM = new_proficiency
            
            # 次の学習時間を計算
            next_datetime = self.datetime_service.calculate_next_datetime(confidence, next_mode, proficiency_MJ, proficiency_JM)

            # 学習データを保存
            result = await self.learn_db.save_learning_data(
                user_id=user_id,
                word_id=word_id,
                level=level,
                proficiency_MJ=proficiency_MJ,
                proficiency_JM=proficiency_JM,
                next_mode=next_mode,
                next_datetime=next_datetime
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error recording learning data: {str(e)}")
            raise
