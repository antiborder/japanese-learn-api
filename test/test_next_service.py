from datetime import datetime, timezone, timedelta

from conftest import insert_words, insert_user_history
from services.next_service import NextService


def _future(minutes: int = 60) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def _past(minutes: int = 60) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()


class TestGetOtherWords:
    async def test_returns_three_ids_excluding_answer(self, dynamodb_table):
        insert_words(dynamodb_table, [
            {"id": 1, "name": "犬", "level": 3, "english": "dog"},
            {"id": 2, "name": "猫", "level": 3, "english": "cat"},
            {"id": 3, "name": "鳥", "level": 3, "english": "bird"},
            {"id": 4, "name": "魚", "level": 3, "english": "fish"},
        ])
        service = NextService()
        result = await service.get_other_words(level=3, exclude_id=1)

        assert len(result) == 3
        assert 1 not in result

    async def test_insufficient_words_returns_empty(self, dynamodb_table):
        insert_words(dynamodb_table, [
            {"id": 1, "name": "犬", "level": 5, "english": "dog"},
            {"id": 2, "name": "猫", "level": 5, "english": "cat"},
        ])
        service = NextService()
        result = await service.get_other_words(level=5, exclude_id=1)

        assert result == []

    async def test_no_words_returns_empty(self, dynamodb_table):
        service = NextService()
        result = await service.get_other_words(level=7, exclude_id=1)

        assert result == []


class TestGetNextWord:
    async def test_new_user_gets_word_from_level(self, dynamodb_table):
        insert_words(dynamodb_table, [
            {"id": 10, "name": "山", "level": 2, "english": "mountain"},
            {"id": 11, "name": "川", "level": 2, "english": "river"},
        ])
        service = NextService()
        result = await service.get_next_word(user_id="new@example.com", level=2)

        assert result is not None
        assert result["answer_word_id"] in [10, 11]

    async def test_no_words_in_level_returns_none(self, dynamodb_table):
        service = NextService()
        result = await service.get_next_word(user_id="user@example.com", level=99)

        assert result is None

    async def test_review_all_returns_oldest_word(self, dynamodb_table):
        insert_user_history(dynamodb_table, "user@example.com", [
            {"word_id": 1, "level": 1, "next_datetime": _past(120), "next_mode": "MJ"},
            {"word_id": 2, "level": 2, "next_datetime": _past(30),  "next_mode": "JM"},
        ])
        service = NextService()
        result = await service.get_next_word(user_id="user@example.com", level="REVIEW_ALL")

        assert result is not None
        assert result["answer_word_id"] == 1  # 120分前 = 最も古い

    async def test_review_all_no_history_returns_none(self, dynamodb_table):
        service = NextService()
        result = await service.get_next_word(user_id="nobody@example.com", level="REVIEW_ALL")

        assert result is None

    async def test_review_all_all_future_returns_no_word_available(self, dynamodb_table):
        insert_user_history(dynamodb_table, "user@example.com", [
            {"word_id": 1, "level": 1, "next_datetime": _future(60)},
            {"word_id": 2, "level": 1, "next_datetime": _future(120)},
        ])
        service = NextService()
        result = await service.get_next_word(user_id="user@example.com", level="REVIEW_ALL")

        assert result is not None
        assert result.get("no_word_available") is True
        assert result.get("next_available_datetime") is not None
