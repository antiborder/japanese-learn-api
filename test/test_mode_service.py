from decimal import Decimal
from unittest.mock import patch
from services.mode_service import ModeService


class TestDetermineNextMode:
    def setup_method(self):
        self.service = ModeService()

    def test_mj_far_below_always_returns_mj(self):
        # MJが低すぎる（差 <= -0.4）→ 必ずMJ
        result = self.service.determine_next_mode(
            proficiency_MJ=Decimal("0.0"),
            proficiency_JM=Decimal("0.5"),
        )
        assert result == "MJ"

    def test_jm_far_below_always_returns_jm(self):
        # JMが低すぎる（差 >= 0.4）→ 必ずJM
        result = self.service.determine_next_mode(
            proficiency_MJ=Decimal("0.5"),
            proficiency_JM=Decimal("0.0"),
        )
        assert result == "JM"

    def test_equal_proficiency_random(self):
        # 等しい場合 jm_probability=0.5。random < 0.5 → JM、random >= 0.5 → MJ
        with patch("services.mode_service.random.random", return_value=0.1):
            result = self.service.determine_next_mode(Decimal("0.5"), Decimal("0.5"))
            assert result == "JM"

        with patch("services.mode_service.random.random", return_value=0.9):
            result = self.service.determine_next_mode(Decimal("0.5"), Decimal("0.5"))
            assert result == "MJ"

    def test_boundary_negative_threshold(self):
        # 差がちょうど -0.4 → MJ
        result = self.service.determine_next_mode(
            proficiency_MJ=Decimal("0.1"),
            proficiency_JM=Decimal("0.5"),
        )
        assert result == "MJ"

    def test_boundary_positive_threshold(self):
        # 差がちょうど 0.4 → JM
        result = self.service.determine_next_mode(
            proficiency_MJ=Decimal("0.5"),
            proficiency_JM=Decimal("0.1"),
        )
        assert result == "JM"
