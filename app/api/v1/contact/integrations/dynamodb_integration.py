import boto3
import os
import logging
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)

TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "")


def _table():
    dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "ap-northeast-1"))
    return dynamodb.Table(TABLE_NAME)


def _generate_id() -> str:
    # タイムスタンプ + uuid4 で時系列ソート可能なIDを生成
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"{ts}-{uuid.uuid4().hex[:12]}"


def save_contact(category: str, email: str, subject: str, body: str, lang: str, is_authenticated: bool) -> str:
    contact_id = _generate_id()
    pk = f"CONTACT#{contact_id}"
    now = datetime.now(timezone.utc).isoformat()

    _table().put_item(
        Item={
            "PK": pk,
            "SK": "METADATA",
            "category": category,
            "email": email,
            "subject": subject,
            "body": body,
            "lang": lang,
            "status": "open",
            "created_at": now,
            "is_authenticated": is_authenticated,
        }
    )

    logger.info(f"Contact saved: {pk}")
    return contact_id


def check_rate_limit(ip: str, limit: int = 5, window_seconds: int = 3600) -> bool:
    """Trueなら制限内（送信可）、Falseなら制限超過"""
    pk = f"RATE_LIMIT#CONTACT#{ip}"
    sk = "COUNT"
    now = int(datetime.now(timezone.utc).timestamp())
    expire_at = now + window_seconds

    table = _table()
    try:
        response = table.get_item(Key={"PK": pk, "SK": sk})
        item = response.get("Item")

        if item is None:
            table.put_item(Item={"PK": pk, "SK": sk, "count": 1, "TTL": expire_at})
            return True

        count = int(item.get("count", 0))
        if count >= limit:
            return False

        table.update_item(
            Key={"PK": pk, "SK": sk},
            UpdateExpression="SET #c = #c + :inc",
            ExpressionAttributeNames={"#c": "count"},
            ExpressionAttributeValues={":inc": 1},
        )
        return True
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        return True  # エラー時は通過させる
