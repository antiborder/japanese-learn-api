from datetime import datetime, timezone, timedelta
from services.datetime_utils import DateTimeUtils


class TestParseDatetimeSafe:
    def test_valid_iso_with_timezone(self):
        result = DateTimeUtils.parse_datetime_safe("2024-01-15T10:00:00+00:00")
        assert result is not None
        assert result.tzinfo is not None

    def test_valid_iso_without_timezone_becomes_utc(self):
        result = DateTimeUtils.parse_datetime_safe("2024-01-15T10:00:00")
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_invalid_format_returns_none(self):
        assert DateTimeUtils.parse_datetime_safe("not-a-date") is None

    def test_none_returns_none(self):
        assert DateTimeUtils.parse_datetime_safe(None) is None


class TestIsReviewable:
    def test_past_datetime_is_reviewable(self):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        word = {"next_datetime": past}
        assert DateTimeUtils.is_reviewable(word) is True

    def test_future_datetime_is_not_reviewable(self):
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        word = {"next_datetime": future}
        assert DateTimeUtils.is_reviewable(word) is False

    def test_missing_next_datetime_returns_false(self):
        assert DateTimeUtils.is_reviewable({}) is False

    def test_invalid_datetime_returns_false(self):
        assert DateTimeUtils.is_reviewable({"next_datetime": "invalid"}) is False


class TestGetNextAvailableTime:
    def test_empty_list_returns_none(self):
        assert DateTimeUtils.get_next_available_time([]) is None

    def test_returns_earliest_datetime(self):
        words = [
            {"next_datetime": "2024-01-15T12:00:00+00:00"},
            {"next_datetime": "2024-01-15T10:00:00+00:00"},
            {"next_datetime": "2024-01-15T14:00:00+00:00"},
        ]
        result = DateTimeUtils.get_next_available_time(words)
        assert result is not None
        assert result.hour == 10
