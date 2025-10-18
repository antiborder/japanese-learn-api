import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict
from .base import DynamoDBBase
from services.datetime_utils import DateTimeUtils

logger = logging.getLogger(__name__)

class PlanDynamoDB(DynamoDBBase):
    def __init__(self):
        super().__init__()
        self.datetime_utils = DateTimeUtils()

    async def get_plan(self, current_user_id: str) -> List[Dict]:
        """
        ログインユーザーの学習計画を返す（24時間スロット別の復習予定数）
        """
        try:
            # ユーザーの学習履歴を全て取得
            user_response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f"USER#{current_user_id}",
                    ':sk_prefix': 'WORD#'
                }
            )
            user_items = user_response.get('Items', [])
            now = datetime.now(timezone.utc)
            
            # 24時間スロット別に復習予定を集計
            time_slots = {}
            
            for item in user_items:
                if 'next_datetime' in item:
                    next_dt = self.datetime_utils.parse_datetime_safe(item['next_datetime'])
                if next_dt is None:
                    logger.warning(f"Invalid next_datetime format for word {item.get('word_id')}")
                    continue
                
                # 現在時刻からの時間差を計算（分単位）
                time_diff_minutes = (next_dt - now).total_seconds() / 60
                
                # 24時間スロットを計算（0は過去、1は0-24時間後、2は24-48時間後...）
                if time_diff_minutes <= 0:
                    time_slot = 0  # 過去（復習可能）
                else:
                    time_slot = int(time_diff_minutes // (24 * 60)) + 1
                
                time_slots[time_slot] = time_slots.get(time_slot, 0) + 1
            
            # 結果をリスト形式で返す（time_slot: 0は必ず含める）
            result = []
            max_slot = max(time_slots.keys()) if time_slots else 0
            
            for slot in range(max_slot + 1):
                result.append({
                    "time_slot": slot,
                    "count": time_slots.get(slot, 0)
                })
            
            # time_slot: 0が存在しない場合は追加
            if not any(item["time_slot"] == 0 for item in result):
                result.append({
                    "time_slot": 0,
                    "count": 0
                })
            
            # time_slotでソート
            result.sort(key=lambda x: x["time_slot"])
            
            logger.info(f"Generated plan for user {current_user_id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in get_plan: {str(e)}")
            raise
