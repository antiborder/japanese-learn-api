import logging
from datetime import datetime, timezone
from typing import Dict, List

from .base import DynamoDBBase
from services.datetime_utils import DateTimeUtils

logger = logging.getLogger(__name__)


class KanaPlanDynamoDB(DynamoDBBase):
    def __init__(self) -> None:
        super().__init__()
        self.datetime_utils = DateTimeUtils()

    async def get_plan(self, current_user_id: str) -> List[Dict]:
        """
        ログインユーザーのかな学習計画を返す（24時間スロット別の復習予定数）
        """
        try:
            user_response = self.table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": f"USER#{current_user_id}",
                    ":sk_prefix": "KANA#",
                },
            )
            user_items = user_response.get("Items", [])
            now = datetime.now(timezone.utc)

            time_slots: Dict[int, int] = {}

            for item in user_items:
                if "next_datetime" not in item:
                    continue

                next_dt = self.datetime_utils.parse_datetime_safe(item["next_datetime"])
                if next_dt is None:
                    logger.warning(
                        "Invalid next_datetime format for kana %s",
                        item.get("char") or item.get("character"),
                    )
                    continue

                time_diff_minutes = (next_dt - now).total_seconds() / 60

                if time_diff_minutes <= 0:
                    time_slot = 0
                else:
                    time_slot = int(time_diff_minutes // (24 * 60)) + 1

                time_slots[time_slot] = time_slots.get(time_slot, 0) + 1

            result: List[Dict[str, int]] = []
            max_slot = max(time_slots.keys()) if time_slots else 0

            for slot in range(max_slot + 1):
                result.append(
                    {
                        "time_slot": slot,
                        "count": time_slots.get(slot, 0),
                    }
                )

            if not any(item["time_slot"] == 0 for item in result):
                result.append(
                    {
                        "time_slot": 0,
                        "count": 0,
                    }
                )

            result.sort(key=lambda x: x["time_slot"])

            logger.info("Generated kana plan for user %s: %s", current_user_id, result)
            return result

        except Exception as exc:
            logger.error("Error in get_kana_plan: %s", exc)
            raise


