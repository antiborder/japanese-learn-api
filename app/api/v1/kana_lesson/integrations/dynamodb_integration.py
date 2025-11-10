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
            return response.get("Items", [])
        except ClientError as exc:
            logger.error(
                "Error querying kana learning data for user %s: %s", user_id, exc
            )
            return []


