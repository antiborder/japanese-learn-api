import boto3
import os
from typing import List, Optional
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class DynamoDBComponent:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(os.environ['DYNAMODB_TABLE_NAME'])

    def get_components(self, skip: int = 0, limit: int = 100) -> List[dict]:
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': 'COMPONENT'
                },
                Limit=limit
            )
            items = response.get('Items', [])
            return items[skip:skip + limit]
        except ClientError as e:
            logger.error(f"Error getting all components from DynamoDB: {str(e)}")
            raise

    def get_component(self, component_id: str) -> Optional[dict]:
        try:
            response = self.table.get_item(
                Key={
                    'PK': 'COMPONENT',
                    'SK': component_id
                }
            )
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting component {component_id} from DynamoDB: {str(e)}")
            raise

component_db = DynamoDBComponent() 