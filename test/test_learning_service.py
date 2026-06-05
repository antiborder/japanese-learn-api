from datetime import datetime, timezone, timedelta
from decimal import Decimal

from services.learning_service import LearningService


class TestRecordLearning:
    """LearningService.record_learning() のテスト。
    dynamodb_table fixture が moto コンテキストを管理する。
    """

    async def test_empty_user_id_skips_dynamodb(self, dynamodb_table):
        """user_idが空の場合DynamoDB書き込みをスキップしデフォルト値を返す"""
        service = LearningService()
        result = await service.record_learning(
            user_id="", word_id=1, level=5, confidence=2, time=Decimal("5")
        )

        assert result["word_id"] == 1
        assert result["next_mode"] == "MJ"
        assert result["proficiency_MJ"] == Decimal("0")
        # DBには何も書かれていないはず
        response = dynamodb_table.get_item(Key={"PK": "USER#", "SK": "WORD#1"})
        assert "Item" not in response

    async def test_new_user_creates_record(self, dynamodb_table):
        """初回学習：DynamoDBに新規レコードが作成される"""
        service = LearningService()
        result = await service.record_learning(
            user_id="test@example.com",
            word_id=42,
            level=3,
            confidence=2,
            time=Decimal("4"),
        )

        assert result["user_id"] == "test@example.com"
        assert result["word_id"] == 42
        assert result["level"] == 3
        assert result["next_mode"] in ("MJ", "JM")
        assert Decimal("0") <= result["proficiency_MJ"] <= Decimal("1")
        assert Decimal("0") <= result["proficiency_JM"] <= Decimal("1")

        item = dynamodb_table.get_item(
            Key={"PK": "USER#test@example.com", "SK": "WORD#42"}
        )["Item"]
        assert item["word_id"] == 42
        assert item["level"] == 3
        assert "next_datetime" in item
        assert "updated_at" in item

    async def test_existing_user_updates_record(self, dynamodb_table):
        """2回目の学習：既存レコードが更新される"""
        service = LearningService()
        await service.record_learning(
            user_id="test@example.com", word_id=10, level=2, confidence=1, time=Decimal("6")
        )
        await service.record_learning(
            user_id="test@example.com", word_id=10, level=2, confidence=3, time=Decimal("2")
        )

        item = dynamodb_table.get_item(
            Key={"PK": "USER#test@example.com", "SK": "WORD#10"}
        )["Item"]
        pMJ = Decimal(str(item["proficiency_MJ"]))
        pJM = Decimal(str(item["proficiency_JM"]))
        assert pMJ + pJM > Decimal("0")

    async def test_confidence_0_sets_short_interval(self, dynamodb_table):
        """confidence=0 のとき、5分後に次の学習時間が設定される"""
        service = LearningService()
        result = await service.record_learning(
            user_id="test@example.com", word_id=99, level=1, confidence=0, time=Decimal("8")
        )

        now = datetime.now(timezone.utc)
        next_dt = result["next_datetime"]
        # 5分後（±30秒の誤差を許容）
        assert timedelta(minutes=4, seconds=30) < (next_dt - now) < timedelta(minutes=5, seconds=30)

    async def test_multiple_users_independent(self, dynamodb_table):
        """異なるユーザーのデータが互いに干渉しない"""
        service = LearningService()
        await service.record_learning("user_a@example.com", 1, 1, 2, Decimal("5"))
        await service.record_learning("user_b@example.com", 1, 1, 3, Decimal("2"))

        item_a = dynamodb_table.get_item(
            Key={"PK": "USER#user_a@example.com", "SK": "WORD#1"}
        )["Item"]
        item_b = dynamodb_table.get_item(
            Key={"PK": "USER#user_b@example.com", "SK": "WORD#1"}
        )["Item"]

        assert item_a["user_id"] == "user_a@example.com"
        assert item_b["user_id"] == "user_b@example.com"
