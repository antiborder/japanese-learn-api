import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import math
from typing import Optional

logger = logging.getLogger(__name__)


class DateTimeService:
    BASE_HOURS = 6

    def calculate_next_datetime(
        self, confidence: int, proficiency: Decimal, reviewable_count: int = 0
    ) -> datetime:
        if confidence == 0:
            return datetime.now(timezone.utc) + timedelta(minutes=5)

        minutes = float(self.BASE_HOURS * 60 * 2 ** (8 * float(proficiency)))
        factor = self._calculate_factor(reviewable_count)
        minutes *= factor

        logger.info(
            "Calculated next datetime for proficiency=%s reviewable_count=%s factor=%s minutes=%s",
            proficiency,
            reviewable_count,
            factor,
            minutes,
        )

        return datetime.now(timezone.utc) + timedelta(minutes=minutes)

    def _calculate_factor(self, reviewable_count: int) -> float:
        if reviewable_count <= 100:
            return 1.0
        if reviewable_count <= 500:
            return (reviewable_count + 100) / 200
        return 3.0

    def calculate_interval_point(self, previous_datetime: Optional[datetime]) -> Decimal:
        if previous_datetime is None:
            return Decimal("0")

        if previous_datetime.tzinfo is None:
            previous_datetime = previous_datetime.replace(tzinfo=timezone.utc)

        current_datetime = datetime.now(timezone.utc)
        previous_interval = (current_datetime - previous_datetime).total_seconds()

        interval_point = Decimal(
            str(max(0, min(1, math.log2(previous_interval / (self.BASE_HOURS * 60)) / 8)))
        )
        return interval_point
