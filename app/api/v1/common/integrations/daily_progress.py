import logging
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from boto3.dynamodb.conditions import Key

import boto3

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))


class DailyProgressDynamoDB:
    def __init__(self):
        self.table_name = os.getenv("DYNAMODB_TABLE_NAME", "japanese-learn-table")
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)

    def _today_jst(self) -> str:
        return datetime.now(JST).strftime("%Y-%m-%d")

    def _ttl_90days(self) -> int:
        return int(time.time()) + 90 * 24 * 60 * 60

    def increment(self, user_id: str) -> None:
        """
        今日の回答数を +1 する。レコードが存在しない場合は作成する。
        ゴール達成判定は GET 側で行うためここでは行わない。
        """
        try:
            today = self._today_jst()
            now_iso = datetime.now(timezone.utc).isoformat()
            self.table.update_item(
                Key={"PK": f"USER#{user_id}", "SK": f"PROGRESS#{today}"},
                UpdateExpression="ADD questions_answered :one SET updated_at = :now, #ttl = :ttl",
                ExpressionAttributeNames={"#ttl": "TTL"},
                ExpressionAttributeValues={
                    ":one": 1,
                    ":now": now_iso,
                    ":ttl": self._ttl_90days(),
                },
            )
        except Exception as e:
            logger.error(f"Error incrementing daily progress for user {user_id}: {e}")

    def get(self, user_id: str) -> Optional[dict]:
        """今日の進捗レコードを返す。レコードがなければ None。"""
        try:
            today = self._today_jst()
            response = self.table.get_item(Key={"PK": f"USER#{user_id}", "SK": f"PROGRESS#{today}"})
            return response.get("Item")
        except Exception as e:
            logger.error(f"Error getting daily progress for user {user_id}: {e}")
            return None

    def get_all(self, user_id: str) -> list:
        """全 PROGRESS レコードを返す（ストリーク計算用）。"""
        try:
            response = self.table.query(
                KeyConditionExpression=Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with("PROGRESS#"),
            )
            return response.get("Items", [])
        except Exception as e:
            logger.error(f"Error getting all daily progress for user {user_id}: {e}")
            return []
