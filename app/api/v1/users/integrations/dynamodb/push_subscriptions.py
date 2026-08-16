import hashlib
import logging
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from .base import DynamoDBBase

logger = logging.getLogger(__name__)


class PushSubscriptionsDynamoDB(DynamoDBBase):
    def __init__(self):
        super().__init__()

    def _sk(self, endpoint: str) -> str:
        return "PUSH_SUB#" + hashlib.sha256(endpoint.encode()).hexdigest()[:16]

    async def save(self, user_id: str, endpoint: str, p256dh: str, auth: str) -> None:
        try:
            now = datetime.now(timezone.utc).isoformat()
            self.table.put_item(
                Item={
                    "PK": f"USER#{user_id}",
                    "SK": self._sk(endpoint),
                    "endpoint": endpoint,
                    "p256dh": p256dh,
                    "auth": auth,
                    "created_at": now,
                }
            )
        except Exception as e:
            logger.error(f"Error saving push subscription for user {user_id}: {e}")
            raise

    async def delete(self, user_id: str, endpoint: str) -> None:
        try:
            self.table.delete_item(
                Key={
                    "PK": f"USER#{user_id}",
                    "SK": self._sk(endpoint),
                }
            )
        except Exception as e:
            logger.error(f"Error deleting push subscription for user {user_id}: {e}")
            raise

    async def get_all(self, user_id: str) -> list:
        try:
            response = self.table.query(
                KeyConditionExpression=Key("PK").eq(f"USER#{user_id}") & Key("SK").begins_with("PUSH_SUB#"),
            )
            return response.get("Items", [])
        except Exception as e:
            logger.error(f"Error getting push subscriptions for user {user_id}: {e}")
            return []
