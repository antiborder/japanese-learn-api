from datetime import datetime, timezone, timedelta

from conftest import insert_words, insert_user_history


def _past(hours: int = 1) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def _future(hours: int = 1) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


class TestGetProgress:
    async def test_new_user_all_zeros(self, dynamodb_table, users_module):
        """学習履歴なし: 全レベルでlearned=0、progress=0"""
        from integrations.dynamodb.progress import ProgressDynamoDB
        insert_words(dynamodb_table, [
            {"id": 1, "name": "犬", "level": 1},
            {"id": 2, "name": "猫", "level": 1},
            {"id": 3, "name": "山", "level": 2},
        ])
        db = ProgressDynamoDB()
        result = await db.get_progress("new@example.com")

        level1 = next(r for r in result if r["level"] == 1)
        assert level1["learned"] == 0
        assert level1["unlearned"] == 2
        assert level1["progress"] == 0
        assert level1["reviewable"] == 0

    async def test_learned_words_appear_in_progress(self, dynamodb_table, users_module):
        """学習済み単語が learned にカウントされる"""
        from integrations.dynamodb.progress import ProgressDynamoDB
        insert_words(dynamodb_table, [
            {"id": 1, "name": "犬", "level": 1},
            {"id": 2, "name": "猫", "level": 1},
            {"id": 3, "name": "鳥", "level": 1},
        ])
        insert_user_history(dynamodb_table, "user@example.com", [
            {"word_id": 1, "level": 1, "next_datetime": _future(),
             "proficiency_MJ": "0.5", "proficiency_JM": "0.3"},
        ])
        db = ProgressDynamoDB()
        result = await db.get_progress("user@example.com")

        level1 = next(r for r in result if r["level"] == 1)
        assert level1["learned"] == 1
        assert level1["unlearned"] == 2
        assert level1["progress"] > 0

    async def test_reviewable_count(self, dynamodb_table, users_module):
        """next_datetimeが過去の単語がreviewableにカウントされる"""
        from integrations.dynamodb.progress import ProgressDynamoDB
        insert_words(dynamodb_table, [
            {"id": 1, "name": "犬", "level": 1},
            {"id": 2, "name": "猫", "level": 1},
        ])
        insert_user_history(dynamodb_table, "user@example.com", [
            {"word_id": 1, "level": 1, "next_datetime": _past(2)},   # 復習可能
            {"word_id": 2, "level": 1, "next_datetime": _future(2)},  # まだ不可
        ])
        db = ProgressDynamoDB()
        result = await db.get_progress("user@example.com")

        level1 = next(r for r in result if r["level"] == 1)
        assert level1["reviewable"] == 1

    async def test_group_filter_n5(self, dynamodb_table, users_module):
        """group=N5 を指定するとレベル1,2,3のみ返る"""
        from integrations.dynamodb.progress import ProgressDynamoDB
        db = ProgressDynamoDB()
        result = await db.get_progress("user@example.com", group="N5")

        levels = [r["level"] for r in result]
        assert levels == [1, 2, 3]

    async def test_invalid_group_raises(self, dynamodb_table, users_module):
        """不正なgroupはValueErrorを送出する"""
        import pytest
        from integrations.dynamodb.progress import ProgressDynamoDB
        db = ProgressDynamoDB()
        with pytest.raises(ValueError):
            await db.get_progress("user@example.com", group="N99")

    async def test_all_learned_full_progress(self, dynamodb_table, users_module):
        """全単語を学習済みかつ高習熟度 → progress が高くなる"""
        from integrations.dynamodb.progress import ProgressDynamoDB
        insert_words(dynamodb_table, [{"id": 1, "name": "犬", "level": 1}])
        insert_user_history(dynamodb_table, "user@example.com", [
            {"word_id": 1, "level": 1, "next_datetime": _future(),
             "proficiency_MJ": "0.9", "proficiency_JM": "0.9"},
        ])
        db = ProgressDynamoDB()
        result = await db.get_progress("user@example.com")

        level1 = next(r for r in result if r["level"] == 1)
        assert level1["learned"] == 1
        assert level1["unlearned"] == 0
        assert level1["progress"] > 0
