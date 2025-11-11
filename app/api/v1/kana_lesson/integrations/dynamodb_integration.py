import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DynamoDBKanaLessonClient:
    def __init__(self) -> None:
        self.table_name = os.getenv("DYNAMODB_TABLE_NAME", "japanese-learn-table")
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)

    def get_current_learning_data(self, user_id: str, char: str) -> Optional[Dict]:
        try:
            response = self.table.get_item(
                Key={
                    "PK": f"USER#{user_id}",
                    "SK": f"KANA#{char}",
                }
            )
            return response.get("Item")
        except ClientError as exc:
            logger.error(
                "Error getting current kana learning data for user %s char %s: %s",
                user_id,
                char,
                exc,
            )
            return None

    async def save_learning_data(
        self,
        user_id: str,
        char: str,
        level: int,
        proficiency: Decimal,
        next_datetime: datetime,
    ) -> Dict:
        try:
            now = datetime.now(timezone.utc)
            item = {
                "PK": f"USER#{user_id}",
                "SK": f"KANA#{char}",
                "user_id": user_id,
                "char": char,
                "character": char,
                "level": level,
                "proficiency": proficiency,
                "next_datetime": next_datetime.isoformat(),
                "updated_at": now.isoformat(),
            }

            self.table.put_item(Item=item)

            return {
                "user_id": user_id,
                "char": char,
                "level": level,
                "proficiency": proficiency,
                "next_datetime": next_datetime,
                "updated_at": now,
            }
        except Exception as exc:
            logger.error(
                "Error saving kana learning data for user %s char %s: %s",
                user_id,
                char,
                exc,
            )
            raise

    async def get_user_kana(self, user_id: str) -> List[Dict]:
        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": f"USER#{user_id}",
                    ":sk_prefix": "KANA#",
                },
            )
            items = response.get("Items", [])
            return [self._convert_kana_item(item) for item in items]
        except ClientError as exc:
            logger.error(
                "Error querying kana learning data for user %s: %s", user_id, exc
            )
            return []

    async def get_level_chars(self, level: int) -> List[Dict]:
        """指定されたレベルのかな一覧を取得します"""
        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={
                    ":pk": "KANA",
                },
            )
            items = response.get("Items", [])
            results: List[Dict] = []
            for item in items:
                converted = self._convert_kana_item(item)
                if converted.get("level") == level:
                    results.append(converted)
            return results
        except ClientError as exc:
            logger.error(
                "Error getting kana list for level %s from DynamoDB: %s", level, exc
            )
            return []
        except Exception as exc:
            logger.error(
                "Unexpected error getting kana list for level %s: %s", level, exc
            )
            raise

    async def get_char_detail(self, char: str) -> Optional[Dict]:
        """かなの詳細を取得します"""
        try:
            response = self.table.get_item(
                Key={
                    "PK": "KANA",
                    "SK": char,
                }
            )
            item = response.get("Item")
            if not item:
                return None
            return self._convert_kana_item(item)
        except ClientError as exc:
            logger.error("Error getting kana detail for char %s: %s", char, exc)
            return None
        except Exception as exc:
            logger.error(
                "Unexpected error getting kana detail for char %s: %s", char, exc
            )
            raise

    def _convert_kana_item(self, item: Dict) -> Dict:
        """DynamoDBアイテムをアプリ内で扱いやすい形式へ変換します"""
        from decimal import Decimal as _Decimal

        char_value = (
            item.get("char")
            or item.get("character")
            or (item.get("SK").split("#")[-1] if item.get("SK") else None)
        )

        level_value = item.get("level")
        if isinstance(level_value, _Decimal):
            level_value = int(level_value)
        elif isinstance(level_value, str) and level_value.lstrip("-").isdigit():
            level_value = int(level_value)

        proficiency_value = item.get("proficiency")
        if isinstance(proficiency_value, _Decimal):
            proficiency_value = proficiency_value

        next_datetime_value = item.get("next_datetime")
        result: Dict = {
            "char": char_value,
            "level": level_value,
        }
        if proficiency_value is not None:
            result["proficiency"] = proficiency_value
        if next_datetime_value is not None:
            result["next_datetime"] = next_datetime_value
        if "updated_at" in item:
            result["updated_at"] = item["updated_at"]

        return result


