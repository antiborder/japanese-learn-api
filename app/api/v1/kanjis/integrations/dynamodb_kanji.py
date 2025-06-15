import boto3
import os
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class DynamoDBKanjiClient:
    def __init__(self):
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.table_name)

    def get_kanji_by_id(self, kanji_id: int):
        try:
            response = self.table.get_item(
                Key={
                    'PK': 'KANJI',
                    'SK': str(kanji_id)
                }
            )
            item = response.get('Item')
            if not item:
                raise HTTPException(status_code=404, detail='Kanji not found')
            
            # idフィールドを追加
            item['id'] = kanji_id
            return item
        except Exception as e:
            logger.error(f"Error getting kanji {kanji_id} from DynamoDB: {str(e)}")
            raise

    def get_all_kanjis(self):
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': 'KANJI'
                }
            )
            items = response.get('Items', [])
            # 各アイテムにidフィールドを追加
            for item in items:
                kanji_id = int(item['SK'])
                item['id'] = kanji_id
            return items
        except Exception as e:
            logger.error(f"Error getting all kanjis from DynamoDB: {str(e)}")
            raise

dynamodb_kanji_client = DynamoDBKanjiClient() 