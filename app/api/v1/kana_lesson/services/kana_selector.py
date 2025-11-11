import logging
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .datetime_utils import DateTimeUtils

logger = logging.getLogger(__name__)


class KanaSelector:
    @staticmethod
    def _extract_char(item: Dict) -> Optional[str]:
        return item.get("char")

    @staticmethod
    def select_new_char(level_chars: List[Dict], user_chars: List[Dict]) -> Optional[Dict]:
        """未学習のかなを選択します。"""
        learned = {KanaSelector._extract_char(item) for item in user_chars}
        candidates = [
            char for char in level_chars if KanaSelector._extract_char(char) not in learned
        ]
        if not candidates:
            return None
        selected = random.choice(candidates)
        logger.debug("Selected new kana: %s", selected)
        return {"answer_char": KanaSelector._summarize_char(selected)}

    @staticmethod
    def select_review_char(user_level_chars: List[Dict]) -> Optional[Dict]:
        """復習対象のかなを選択します。"""
        reviewable = [
            char for char in user_level_chars if DateTimeUtils.is_reviewable(char)
        ]
        if not reviewable:
            return None
        answer = min(
            reviewable,
            key=lambda item: DateTimeUtils.parse_datetime_safe(item.get("next_datetime"))
            or datetime.min.replace(tzinfo=timezone.utc),
        )
        logger.debug("Selected review kana: %s", answer)
        return {"answer_char": KanaSelector._summarize_char(answer)}

    @staticmethod
    def select_next_char(
        level_chars: List[Dict],
        user_chars: List[Dict],
        user_id: Optional[str],
        level: int,
    ) -> Optional[Dict]:
        """次に提示するかなを選択します。"""
        user_level_chars = [
            item for item in user_chars if item.get("level") == level
        ]

        if not level_chars:
            return None

        ratio = (
            len(user_level_chars) / len(level_chars)
            if level_chars
            else 0
        )

        if random.random() > ratio:
            new_char = KanaSelector.select_new_char(level_chars, user_level_chars)
            if new_char:
                logger.info(
                    "Selected new kana for user %s level %s: %s",
                    user_id,
                    level,
                    new_char,
                )
                return new_char

        review_char = KanaSelector.select_review_char(user_level_chars)
        if review_char:
            logger.info(
                "Selected review kana for user %s level %s: %s",
                user_id,
                level,
                review_char,
            )
            return review_char

        # 復習対象が無ければ再度新規から選定
        new_char = KanaSelector.select_new_char(level_chars, user_level_chars)
        if new_char:
            logger.info(
                "Fallback new kana for user %s level %s: %s",
                user_id,
                level,
                new_char,
            )
            return new_char

        # 復習可能でも新規でもない場合、次に可能な時間を返す
        next_available = DateTimeUtils.get_next_available_time(user_level_chars)
        if next_available:
            logger.info(
                "No kana available for user %s level %s; next available at %s",
                user_id,
                level,
                next_available,
            )
            return {
                "no_char_available": True,
                "next_available_datetime": next_available,
            }

        if level_chars:
            selected = random.choice(level_chars)
            logger.info(
                "Random fallback kana for user %s level %s: %s",
                user_id,
                level,
                selected,
            )
            return {"answer_char": KanaSelector._summarize_char(selected)}

        return None

    @staticmethod
    def _summarize_char(item: Dict) -> Dict:
        return {
            "char": item.get("char"),
            "level": item.get("level"),
        }

