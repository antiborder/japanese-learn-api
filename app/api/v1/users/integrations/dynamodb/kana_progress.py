import logging
from typing import Dict, List, Set

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
            user_items = self._get_user_kana_items(current_user_id)
            master_by_level = self._get_master_kana_by_level()

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
                master_items = master_by_level.get(level, [])
                master_chars: Set[str] = {
                    item.get("char") or item.get("character")
                    for item in master_items
                    if (item.get("char") or item.get("character")) is not None
                }

                learned = sum(
                    1
                    for item in level_items
                    if (item.get("char") or item.get("character")) in master_chars
                )
                total = len(master_chars)
                unlearned = max(total - learned, 0)

                total_proficiency = sum(
                    float(item.get("proficiency", 0)) for item in level_items
                )
                avg_proficiency = (
                    total_proficiency / learned if learned > 0 else 0
                )
                learned_ratio = learned / total if total > 0 else 0
                progress = int(round(learned_ratio * avg_proficiency * 100))

                reviewable = sum(
                    1
                    for item in level_items
                    if self.datetime_utils.is_reviewable(item)
                )

                result.append(
                    {
                        "level": level,
                        "progress": progress,
                        "reviewable": reviewable,
                        "learned": learned,
                        "unlearned": unlearned,
                    }
                )

            logger.info("Generated kana progress for user %s: %s", current_user_id, result)
            return result
        except Exception as exc:
            logger.error("Error in get_kana_progress: %s", exc)
            raise

    def _get_user_kana_items(self, current_user_id: str) -> List[Dict]:
        response = self.table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": f"USER#{current_user_id}",
                ":sk_prefix": "KANA#",
            },
        )
        return response.get("Items", [])

    def _get_master_kana_by_level(self) -> Dict[int, List[Dict]]:
        result: Dict[int, List[Dict]] = {}
        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={":pk": "KANA"},
            )
            items = response.get("Items", [])
            for item in items:
                level = item.get("level")
                if level is None:
                    continue
                try:
                    level_int = int(level)
                except (TypeError, ValueError):
                    logger.warning("Invalid level in kana master item: %s", level)
                    continue
                result.setdefault(level_int, []).append(item)
            return result
        except Exception as exc:
            logger.error("Error fetching kana master data: %s", exc)
            return result

