import logging
from datetime import datetime, timezone
from typing import List, Dict
from .base import DynamoDBBase
from services.datetime_utils import DateTimeUtils
from common.config import MIN_LEVEL, MAX_LEVEL

logger = logging.getLogger(__name__)

class SentencesProgressDynamoDB(DynamoDBBase):
    def __init__(self):
        super().__init__()
        self.datetime_utils = DateTimeUtils()

    async def get_progress(self, current_user_id: str) -> List[Dict]:
        """
        ログインユーザーの例文のレベルごとの進捗情報を返す（unlearnedも含む）
        """
        try:
            # ユーザーの例文学習履歴を全て取得
            user_response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f"USER#{current_user_id}",
                    ':sk_prefix': 'SENTENCE#'
                }
            )
            user_items = user_response.get('Items', [])
            now = datetime.now(timezone.utc)
            result = []
            for level in range(MIN_LEVEL, MAX_LEVEL + 1):
                # 各レベルの全例文をFilterExpressionで取得
                sentence_response = self.table.query(
                    KeyConditionExpression='PK = :pk',
                    FilterExpression='#level = :level',
                    ExpressionAttributeNames={
                        '#level': 'level'
                    },
                    ExpressionAttributeValues={
                        ':pk': 'SENTENCE',
                        ':level': level
                    }
                )
                all_sentence_ids = set(int(item['SK']) for item in sentence_response.get('Items', []))
                # ユーザーの学習済み例文IDリスト
                level_user_items = [item for item in user_items if item.get('level') == level]
                user_learned_ids = set(int(item['sentence_id']) for item in level_user_items)
                learned = len(user_learned_ids)
                unlearned = len(all_sentence_ids - user_learned_ids)
                reviewable = sum(
                    1 for item in level_user_items
                    if self.datetime_utils.is_reviewable(item)
                )
                if level_user_items:
                    # 学習済み例文の習熟度の平均を計算
                    gross_proficiency = sum(float(item.get('proficiency', 0)) for item in level_user_items)
                    avg_proficiency_of_learned = gross_proficiency / learned if learned > 0 else 0
                    
                    # 全体の進捗率を計算（学習済み例文数 / 全例文数）
                    learned_ratio = learned / len(all_sentence_ids) if len(all_sentence_ids) > 0 else 0
                    
                    # 最終的なproficiencyは、完了率と習熟度の平均を組み合わせる
                    # 完了率が高いほど、習熟度の重みが高くなる
                    progress = int(round((learned_ratio * avg_proficiency_of_learned) * 100))
                else:
                    progress = 0
                result.append({
                    "level": level,
                    "progress": progress,
                    "reviewable": reviewable,
                    "learned": learned,
                    "unlearned": unlearned
                })
            return result
        except Exception as e:
            logger.error(f"Error in get_sentences_progress: {str(e)}")
            raise
