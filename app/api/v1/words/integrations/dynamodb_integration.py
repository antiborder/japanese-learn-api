import boto3
import os
import logging
from typing import List, Dict, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class DynamoDBClient:
    def __init__(self):
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.table_name)

    def get_words(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        try:
            response = self.table.scan(
                FilterExpression="begins_with(PK, :prefix)",
                ExpressionAttributeValues={
                    ":prefix": "WORD#"
                },
                Limit=limit
            )
            
            items = response.get('Items', [])
            
            # DynamoDBの結果をMySQLモデルの形式に変換
            words = []
            for item in items:
                try:
                    word = {
                        'id': int(item['PK'].split('#')[1]),  # WORD#1 から 1 を取得
                        'name': item.get('name', ''),
                        'hiragana': item.get('hiragana', ''),
                        'is_katakana': bool(int(item.get('is_katakana', 0))),
                        'level': item.get('level', ''),
                        'english': item.get('english', ''),
                        'vietnamese': item.get('vietnamese', ''),
                        'lexical_category': item.get('lexical_category', ''),
                        'accent_up': int(item.get('accent_up')) if item.get('accent_up') else None,
                        'accent_down': int(item.get('accent_down')) if item.get('accent_down') else None
                    }
                    words.append(word)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting item {item['PK']}: {str(e)}")
                    continue
            
            # スキップとリミットの適用
            return words[skip:skip + limit]
            
        except ClientError as e:
            logger.error(f"Error getting words from DynamoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

dynamodb_client = DynamoDBClient() 