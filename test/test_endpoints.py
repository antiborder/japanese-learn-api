"""
FastAPI エンドポイントテスト (POST /learn_words/, POST /learn_words/next)

TestClient を使い、Cognito認証を dependency_overrides でバイパスする。
DynamoDB は dynamodb_table fixture (moto) でモックする。
"""
from conftest import insert_words, insert_user_history
from datetime import datetime, timezone, timedelta


def _past(hours: int = 1) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def _future(hours: int = 1) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


TEST_USER = "endpoint_test@example.com"


def make_client(dynamodb_table):
    """TestClient を生成し、認証を TEST_USER に固定する。"""
    from fastapi.testclient import TestClient
    from app import app
    from common.auth import get_current_user_id

    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER
    return TestClient(app)


class TestRecordLearningEndpoint:
    """POST /api/v1/learn_words/"""

    def test_record_learning_returns_200(self, dynamodb_table):
        client = make_client(dynamodb_table)
        response = client.post("/api/v1/learn_words/", json={
            "word_id": 1,
            "level": 3,
            "confidence": 2,
            "time": 5.0,
        })
        assert response.status_code == 200

    def test_record_learning_response_has_required_fields(self, dynamodb_table):
        client = make_client(dynamodb_table)
        response = client.post("/api/v1/learn_words/", json={
            "word_id": 42,
            "level": 5,
            "confidence": 3,
            "time": 3.0,
        })
        data = response.json()
        assert "word_id" in data
        assert "next_mode" in data
        assert "next_datetime" in data
        assert data["word_id"] == 42

    def test_record_learning_saves_to_dynamodb(self, dynamodb_table):
        client = make_client(dynamodb_table)
        client.post("/api/v1/learn_words/", json={
            "word_id": 7,
            "level": 2,
            "confidence": 1,
            "time": 8.0,
        })
        item = dynamodb_table.get_item(
            Key={"PK": f"USER#{TEST_USER}", "SK": "WORD#7"}
        ).get("Item")
        assert item is not None
        assert item["word_id"] == 7
        assert item["level"] == 2

    def test_record_learning_without_auth_returns_403(self, dynamodb_table):
        """認証オーバーライドなしで直接呼ぶと 401/403 が返る"""
        from fastapi.testclient import TestClient
        from app import app
        from common.auth import get_current_user_id

        # overrides をリセット
        app.dependency_overrides = {}
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/api/v1/learn_words/", json={
            "word_id": 1, "level": 1, "confidence": 1, "time": 5.0,
        })
        assert response.status_code in (401, 403, 422)


class TestGetNextWordEndpoint:
    """POST /api/v1/learn_words/next"""

    def test_next_word_with_words_in_db(self, dynamodb_table):
        insert_words(dynamodb_table, [
            {"id": 1, "name": "犬", "level": 3, "english": "dog"},
            {"id": 2, "name": "猫", "level": 3, "english": "cat"},
            {"id": 3, "name": "鳥", "level": 3, "english": "bird"},
            {"id": 4, "name": "魚", "level": 3, "english": "fish"},
        ])
        # word details も必要（batch_get_item用）
        for w in [
            {"id": 1, "name": "犬", "english": "dog"}, {"id": 2, "name": "猫", "english": "cat"},
            {"id": 3, "name": "鳥", "english": "bird"}, {"id": 4, "name": "魚", "english": "fish"},
        ]:
            dynamodb_table.put_item(Item={
                "PK": "WORD", "SK": str(w["id"]),
                "name": w["name"], "english": w["english"],
                "hiragana": "", "level": 3,
                "is_katakana": 0, "lexical_category": "",
            })
        client = make_client(dynamodb_table)
        response = client.post("/api/v1/learn_words/next", json={"level": 3})
        assert response.status_code == 200
        data = response.json()
        assert "answer_word" in data
        assert "other_words" in data
        assert len(data["other_words"]) == 3

    def test_next_word_no_words_returns_404(self, dynamodb_table):
        client = make_client(dynamodb_table)
        response = client.post("/api/v1/learn_words/next", json={"level": 99})
        assert response.status_code == 404

    def test_next_word_review_all_no_history_returns_404(self, dynamodb_table):
        client = make_client(dynamodb_table)
        response = client.post("/api/v1/learn_words/next", json={"level": "REVIEW_ALL"})
        assert response.status_code == 404

    def test_next_word_review_all_with_history(self, dynamodb_table):
        insert_user_history(dynamodb_table, TEST_USER, [
            {"word_id": 1, "level": 1, "next_datetime": _past(2)},
            {"word_id": 2, "level": 1, "next_datetime": _past(1)},
        ])
        # 全レベルから other_words を取れるように多めに単語を入れる
        insert_words(dynamodb_table, [
            {"id": i, "name": f"word{i}", "level": 1} for i in range(1, 10)
        ])
        for i in range(1, 10):
            dynamodb_table.put_item(Item={
                "PK": "WORD", "SK": str(i),
                "name": f"word{i}", "hiragana": "", "level": 1,
                "is_katakana": 0, "lexical_category": "",
            })
        client = make_client(dynamodb_table)
        response = client.post("/api/v1/learn_words/next", json={"level": "REVIEW_ALL"})
        # 復習可能な単語あり → 200 または no_word_available 応答
        assert response.status_code in (200, 200)
        data = response.json()
        # 正解単語 or no_word_available を返す
        assert "answer_word" in data or "next_available_datetime" in data
