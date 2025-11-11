import logging
from typing import Dict, List

from .base import DynamoDBBase
from services.datetime_utils import DateTimeUtils

logger = logging.getLogger(__name__)


class KanaProgressDynamoDB(DynamoDBBase):
    LEVELS = [-10, -7]  # ひらがな・カタカナ

    def __init__(self) -> None:
        super().__init__()
        self.datetime_utils = DateTimeUtils()

    async def get_progress(self, current_user_id: str) -> List[Dict]:
        """
        ログインユーザーのかなレベルごとの進捗情報を返す（学習済み／未学習／復習可能）
        レベルは -10（ひらがな）〜0（カタカナ）を想定
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

            user_items_by_level: Dict[int, List[Dict]] = {}
            for item in user_items:
                level = item.get("level")
                if level is None:
                    continue
                try:
                    level_int = int(level)
                except (TypeError, ValueError):
                    logger.warning("Invalid level for kana item: %s", level)
                    continue
                user_items_by_level.setdefault(level_int, []).append(item)

            result: List[Dict] = []
            for level in self.LEVELS:
                level_items = user_items_by_level.get(level, [])
                learned = len(level_items)
                reviewable = sum(
                    1
                    for item in level_items
                    if self.datetime_utils.is_reviewable(item)
                )

                result.append(
                    {
                        "level": level,
                        "progress": 100 if learned > 0 else 0,
                        "reviewable": reviewable,
                        "learned": learned,
                        "unlearned": 0,
                    }
                )

            logger.info("Generated kana progress for user %s: %s", current_user_id, result)
            return result
        except Exception as exc:
            logger.error("Error in get_kana_progress: %s", exc)
            raise

