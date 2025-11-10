import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional

from integrations.dynamodb_integration import DynamoDBKanaLessonClient
from services.proficiency_service import ProficiencyService
from services.datetime_service import DateTimeService

logger = logging.getLogger(__name__)


class LearningService:
    def __init__(self) -> None:
        self.db_client = DynamoDBKanaLessonClient()
        self.proficiency_service = ProficiencyService()
        self.datetime_service = DateTimeService()

    async def record_learning(
        self,
        user_id: str,
        char: str,
        level: int,
        confidence: int,
        time: Decimal,
    ) -> Dict:
        if not user_id:
            logger.info("User ID is null or empty. Skipping DynamoDB record.")
            now = datetime.now(timezone.utc)
            return {
                "user_id": user_id,
                "char": char,
                "level": level,
                "proficiency": Decimal("0"),
                "next_datetime": now,
                "updated_at": now,
            }

        try:
            current_data = self.db_client.get_current_learning_data(user_id, char)

            new_proficiency = self.proficiency_service.calculate_proficiency(
                confidence, time, current_data
            )

            reviewable_count = await self._get_reviewable_count(user_id)

            next_datetime = self.datetime_service.calculate_next_datetime(
                confidence, new_proficiency, reviewable_count
            )

            result = await self.db_client.save_learning_data(
                user_id=user_id,
                char=char,
                level=level,
                proficiency=new_proficiency,
                next_datetime=next_datetime,
            )

            return result
        except Exception as exc:
            logger.error(
                "Error recording kana learning data for user %s char %s: %s",
                user_id,
                char,
                exc,
            )
            raise

    async def _get_reviewable_count(self, user_id: str) -> int:
        try:
            user_items = await self.db_client.get_user_kana(user_id)
            now = datetime.now(timezone.utc)
            reviewable_count = 0

            for item in user_items:
                next_datetime_str: Optional[str] = item.get("next_datetime")
                if not next_datetime_str:
                    continue
                try:
                    next_dt = datetime.fromisoformat(next_datetime_str)
                    if next_dt.tzinfo is None:
                        next_dt = next_dt.replace(tzinfo=timezone.utc)
                    if next_dt <= now:
                        reviewable_count += 1
                except ValueError:
                    logger.debug(
                        "Skipping item with invalid next_datetime for user %s: %s",
                        user_id,
                        next_datetime_str,
                    )
                    continue

            logger.info("User %s has %s reviewable kana", user_id, reviewable_count)
            return reviewable_count
        except Exception as exc:
            logger.error("Error getting reviewable count for user %s: %s", user_id, exc)
            return 0
