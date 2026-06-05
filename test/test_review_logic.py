from datetime import datetime, timezone, timedelta
from services.review_logic import ReviewLogic


def _word(word_id: int, minutes_offset: int, mode: str = "MJ") -> dict:
    """テスト用の単語データを生成する。minutes_offset が負なら過去（復習可能）。"""
    dt = datetime.now(timezone.utc) + timedelta(minutes=minutes_offset)
    return {"word_id": word_id, "next_datetime": dt.isoformat(), "next_mode": mode}


class TestGetReviewableWords:
    def test_all_past_are_reviewable(self):
        words = [_word(1, -60), _word(2, -30)]
        result = ReviewLogic.get_reviewable_words(words)
        assert len(result) == 2

    def test_future_words_excluded(self):
        words = [_word(1, -60), _word(2, 60)]
        result = ReviewLogic.get_reviewable_words(words)
        assert len(result) == 1
        assert result[0]["word_id"] == 1

    def test_empty_list(self):
        assert ReviewLogic.get_reviewable_words([]) == []


class TestGetReviewAllWord:
    def test_no_words_returns_none(self):
        assert ReviewLogic.get_review_all_word([]) is None

    def test_reviewable_words_returns_oldest(self):
        # word_id=1 のほうが古い（= next_datetimeが早い）
        words = [_word(1, -120), _word(2, -30)]
        result = ReviewLogic.get_review_all_word(words)
        assert result is not None
        assert result["answer_word_id"] == 1

    def test_no_reviewable_returns_next_available(self):
        # 全て未来 → no_word_available になる
        words = [_word(1, 60), _word(2, 120)]
        result = ReviewLogic.get_review_all_word(words)
        assert result is not None
        assert result.get("no_word_available") is True
        assert result.get("next_available_datetime") is not None
