import os
import sys

import boto3
import pytest
from moto import mock_aws

BASE = os.path.join(os.path.dirname(__file__), "..", "app")

sys.path.insert(0, os.path.join(BASE, "api", "v1", "learn_words"))
sys.path.insert(0, os.path.join(BASE, "utils"))  # app/utils/utils.py が learn_words/utils/ より優先

TABLE_NAME = "japanese-learn-table"
AWS_REGION = "ap-northeast-1"


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
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.meta.client.get_waiter("table_exists").wait(TableName=TABLE_NAME)

        yield table
