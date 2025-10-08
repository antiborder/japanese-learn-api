import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from decimal import Decimal
from integrations.dynamodb_integration import DynamoDBSentenceCompositionClient
from services.proficiency_service import ProficiencyService
from services.datetime_service import DateTimeService

logger = logging.getLogger(__name__)

class LearningService:
    def __init__(self):
        self.db_client = DynamoDBSentenceCompositionClient()
        self.proficiency_service = ProficiencyService()
        self.datetime_service = DateTimeService()

    async def record_learning(self, 
                            user_id: str, 
                            sentence_id: int, 
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
                    'sentence_id': sentence_id,
                    'level': level,
                    'proficiency': Decimal('0'),
                    'next_datetime': datetime.now(timezone.utc) + timedelta(minutes=5)
                }

            # 現在のデータを取得
            current_data = self.db_client.get_current_learning_data(user_id, sentence_id)
                        
            # 現在のデータがある場合は更新、ない場合は新規作成
            if current_data:
                proficiency = Decimal(str(current_data.get('proficiency', '0')))
            else:
                proficiency = Decimal('0')
            
            # 習熟度を計算
            new_proficiency = self.proficiency_service.calculate_proficiency(confidence, time, current_data)
            
            # 復習可能文数を取得
            reviewable_count = await self._get_reviewable_count(user_id)
            
            # 次の学習時間を計算（復習可能文数による補正を適用）
            next_datetime = self.datetime_service.calculate_next_datetime(
                confidence, 
                new_proficiency, 
                reviewable_count
            )

            # 学習データを保存
            result = await self.db_client.save_learning_data(
                user_id=user_id,
                sentence_id=sentence_id,
                level=level,
                proficiency=new_proficiency,
                next_datetime=next_datetime
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error recording learning data: {str(e)}")
            raise
    
    async def _get_reviewable_count(self, user_id: str) -> int:
        """ユーザーの復習可能文数を取得します
        
        Args:
            user_id: ユーザーID
            
        Returns:
            int: 復習可能文数
        """
        try:
            # ユーザーの全学習履歴を取得
            user_sentences = await self.db_client.get_user_sentences(user_id)
            
            # 復習可能な文をフィルタリング
            now = datetime.now(timezone.utc)
            reviewable_count = 0
            
            for sentence in user_sentences:
                if 'next_datetime' in sentence:
                    next_dt = datetime.fromisoformat(sentence['next_datetime'])
                    if next_dt <= now:
                        reviewable_count += 1
            
            logger.info(f"User {user_id} has {reviewable_count} reviewable sentences")
            
            return reviewable_count
        except Exception as e:
            logger.error(f"Error getting reviewable count: {str(e)}")
            # エラー時はデフォルト値0を返す（Factor=1になる）
            return 0
