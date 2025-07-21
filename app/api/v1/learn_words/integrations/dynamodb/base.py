import boto3
import os
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class DynamoDBBase:
    def __init__(self):
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.table_name)

    def get_item(self, key: dict) -> dict:
        try:
            response = self.table.get_item(Key=key)
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting item: {str(e)}")
            return None 