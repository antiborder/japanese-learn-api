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

    def get_kanjis_by_component_id(self, component_id: str):
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f'COMPONENT#{component_id}'
                }
            )
            items = response.get('Items', [])
            result = []
            for item in items:
                # SKは "KANJI#{kanji_id}" 形式
                kanji_id = item['SK'].replace('KANJI#', '')
                kanji_char = item.get('kanji_char')
                result.append({
                    'kanji_id': kanji_id,
                    'kanji_char': kanji_char
                })
            return result
        except Exception as e:
            logger.error(f"Error getting kanjis for component {component_id} from DynamoDB: {str(e)}")
            raise

component_db = DynamoDBComponent() 