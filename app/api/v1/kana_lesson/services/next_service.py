import logging
import random
from typing import Dict, Optional

from integrations.dynamodb_integration import DynamoDBKanaLessonClient
from .kana_selector import KanaSelector

logger = logging.getLogger(__name__)


class NextService:
    def __init__(self) -> None:
        self.db_client = DynamoDBKanaLessonClient()
        self.selector = KanaSelector()

    async def get_next_char(self, level: int, user_id: Optional[str]) -> Optional[Dict]:
        """次に学習すべきかなを取得します。"""
        try:
            level_chars = await self.db_client.get_level_chars(level)
            if not level_chars:
                logger.info("No kana found for level %s", level)
                return None

            if not user_id:
                selected = random.choice(level_chars)
                logger.info(
                    "User not authenticated, returning random kana %s for level %s",
                    selected,
                    level,
                )
                return {"answer_char": selected}

            user_chars = await self.db_client.get_user_kana(user_id)
            selection = self.selector.select_next_char(
                level_chars, user_chars, user_id, level
            )
            if not selection:
                logger.info(
                    "Kana selection returned empty for user %s level %s",
                    user_id,
                    level,
                )
                return None

            if selection.get("no_char_available"):
                return selection

            answer = selection.get("answer_char")
            if not answer:
                logger.info(
                    "Kana selection missing answer_char for user %s level %s",
                    user_id,
                    level,
                )
                return None

            if "level" not in answer or answer["level"] is None:
                answer["level"] = level

            logger.info(
                "Successfully selected kana for user %s level %s: %s",
                user_id,
                level,
                answer,
            )
            return {"answer_char": answer}
        except Exception as exc:
            logger.error(
                "Error selecting next kana for user %s level %s: %s",
                user_id,
                level,
                exc,
                exc_info=True,
            )
            raise

