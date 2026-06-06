from decimal import Decimal
from datetime import datetime, timezone, timedelta
from services.proficiency_service import ProficiencyService


class TestCalculateProficiency:
    def setup_method(self):
        self.service = ProficiencyService()

    def test_result_is_between_0_and_1(self):
        result = self.service.calculate_proficiency(confidence=2, time=Decimal("5"))
        assert Decimal("0") <= result <= Decimal("1")

    def test_high_confidence_fast_time_gives_higher_score(self):
        high = self.service.calculate_proficiency(confidence=3, time=Decimal("2"))
        low = self.service.calculate_proficiency(confidence=0, time=Decimal("9"))
        assert high > low

    def test_no_previous_data_interval_is_zero(self):
        # current_dataなし → interval_point=0 の分だけスコアが下がる
        result_no_history = self.service.calculate_proficiency(confidence=3, time=Decimal("0"), current_data=None)
        past = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        result_with_history = self.service.calculate_proficiency(
            confidence=3, time=Decimal("0"), current_data={"updated_at": past}
        )
        assert result_with_history > result_no_history

    def test_time_over_limit_clamped_to_zero(self):
        # time >= TIME_LIMIT(10) → time_point=0
        result = self.service.calculate_proficiency(confidence=3, time=Decimal("15"))
        # time_point=0 なので、max confidence でも 0.4*easiness + 0.4*0 + 0.2*0
        assert result <= Decimal("0.9")  # 1.0にはならない
