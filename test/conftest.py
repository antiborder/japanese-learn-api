import os
import sys

import boto3
import pytest
from moto import mock_aws

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
V1 = os.path.join(BASE, "api", "v1")

# learn_words のパスを最初に追加（既存テストが依存）
sys.path.insert(0, os.path.join(V1, "learn_words"))
sys.path.insert(0, os.path.join(V1))           # common.* の解決用
sys.path.insert(0, os.path.join(BASE, "utils"))  # app/utils/utils.py が最優先

TABLE_NAME = "japanese-learn-table"
AWS_REGION = "ap-northeast-1"

# Lambda間で共有される競合パッケージ名
_LAMBDA_PACKAGES = ("integrations", "services", "schemas", "endpoints", "common")


def _save_and_clear_lambda_modules() -> dict:
    """競合するLambdaパッケージのsys.modulesエントリを退避して削除する。"""
    saved = {}
    for key in list(sys.modules.keys()):
        if key.split(".")[0] in _LAMBDA_PACKAGES:
            saved[key] = sys.modules.pop(key)
    return saved


def _restore_lambda_modules(saved: dict) -> None:
    """退避したsys.modulesエントリを復元する。"""
    # テスト中に追加されたモジュールを消す
    for key in list(sys.modules.keys()):
        if key.split(".")[0] in _LAMBDA_PACKAGES:
            del sys.modules[key]
    sys.modules.update(saved)


@pytest.fixture
def dynamodb_table():
    """motoでDynamoDBテーブルを作成するfixture。各テストの前後にリセットされる。"""
    with mock_aws():
        os.environ["DYNAMODB_TABLE_NAME"] = TABLE_NAME
        os.environ["AWS_DEFAULT_REGION"] = AWS_REGION
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"

        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "level", "AttributeType": "N"},
                {"AttributeName": "name", "AttributeType": "S"},
                {"AttributeName": "english", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "word-level-index",
                    "KeySchema": [
                        {"AttributeName": "PK", "KeyType": "HASH"},
                        {"AttributeName": "level", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "user-level-index",
                    "KeySchema": [
                        {"AttributeName": "PK", "KeyType": "HASH"},
                        {"AttributeName": "level", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "name-index",
                    "KeySchema": [
                        {"AttributeName": "name", "KeyType": "HASH"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "english-index",
                    "KeySchema": [
                        {"AttributeName": "english", "KeyType": "HASH"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.meta.client.get_waiter("table_exists").wait(TableName=TABLE_NAME)
        yield table


@pytest.fixture
def users_module(monkeypatch):
    """users Lambdaのパスを優先するfixture。learn_wordsとの競合を分離する。"""
    users_path = os.path.join(V1, "users")
    saved = _save_and_clear_lambda_modules()
    monkeypatch.syspath_prepend(users_path)
    yield
    _restore_lambda_modules(saved)


@pytest.fixture
def search_module(monkeypatch):
    """search Lambdaのパスを優先するfixture。learn_wordsとの競合を分離する。"""
    search_path = os.path.join(V1, "search")
    saved = _save_and_clear_lambda_modules()
    monkeypatch.syspath_prepend(search_path)
    yield
    _restore_lambda_modules(saved)


# ─── テストデータ挿入ヘルパー ─────────────────────────────────────────────────

def insert_words(table, words: list[dict]) -> None:
    """単語マスタをテーブルに挿入する。
    GSIキー（name, english）は空文字を許容しないため、値があるときだけ追加する。
    """
    for w in words:
        item = {
            "PK": "WORD",
            "SK": str(w["id"]),
            "name": w["name"],
            "hiragana": w.get("hiragana", ""),
            "level": w["level"],
            "is_katakana": 0,
            "lexical_category": w.get("lexical_category", ""),
        }
        if w.get("english"):
            item["english"] = w["english"]
        table.put_item(Item=item)


def insert_user_history(table, user_id: str, entries: list[dict]) -> None:
    """ユーザー学習履歴をテーブルに挿入する。"""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    for e in entries:
        table.put_item(Item={
            "PK": f"USER#{user_id}",
            "SK": f"WORD#{e['word_id']}",
            "user_id": user_id,
            "word_id": e["word_id"],
            "level": e["level"],
            "next_datetime": e["next_datetime"],
            "next_mode": e.get("next_mode", "MJ"),
            "proficiency_MJ": e.get("proficiency_MJ", "0"),
            "proficiency_JM": e.get("proficiency_JM", "0"),
            "updated_at": now,
        })
