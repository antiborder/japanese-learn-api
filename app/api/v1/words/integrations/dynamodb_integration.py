import boto3
import os
import logging
from typing import List, Dict, Optional
from botocore.exceptions import ClientError
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class DynamoDBClient:
    def __init__(self):
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.table_name)

    def get_words(self, skip: int = 0, limit: int = 100, level: Optional[int] = None) -> List[Dict]:
        """
        単語一覧を取得します（レベルフィルタ対応）
        
        Args:
            skip: スキップする件数
            limit: 取得する最大件数
            level: レベルフィルタ（オプション）
        """
        try:
            # すべての単語を取得（DynamoDBのqueryはページネーションが必要な場合がある）
            all_items = []
            last_evaluated_key = None
            
            while True:
                query_params = {
                    "KeyConditionExpression": "PK = :pk",
                    "ExpressionAttributeValues": {
                        ":pk": "WORD"
                    }
                }
                
                # レベルフィルタを適用
                if level is not None:
                    query_params["FilterExpression"] = "#level = :level"
                    query_params["ExpressionAttributeNames"] = {
                        "#level": "level"
                    }
                    query_params["ExpressionAttributeValues"][":level"] = level
                
                if last_evaluated_key:
                    query_params["ExclusiveStartKey"] = last_evaluated_key
                
                response = self.table.query(**query_params)
                items = response.get('Items', [])
                all_items.extend(items)
                
                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break
            
            # アイテムを変換
            words = []
            for item in all_items:
                try:
                    word = self._convert_dynamodb_to_model(item)
                    words.append(word)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting item {item['SK']}: {str(e)}")
                    continue
            
            # skip/limitを適用
            return words[skip:skip + limit]
        except ClientError as e:
            logger.error(f"Error getting words from DynamoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

    def count_words(self, level: Optional[int] = None) -> int:
        """
        単語の総件数を取得します（レベルフィルタ対応）
        
        Args:
            level: レベルフィルタ（オプション）
        """
        try:
            count = 0
            last_evaluated_key = None
            
            while True:
                query_params = {
                    "KeyConditionExpression": "PK = :pk",
                    "ExpressionAttributeValues": {
                        ":pk": "WORD"
                    },
                    "Select": "COUNT"
                }
                
                # レベルフィルタを適用
                if level is not None:
                    query_params["FilterExpression"] = "#level = :level"
                    query_params["ExpressionAttributeNames"] = {
                        "#level": "level"
                    }
                    query_params["ExpressionAttributeValues"][":level"] = level
                
                if last_evaluated_key:
                    query_params["ExclusiveStartKey"] = last_evaluated_key
                
                response = self.table.query(**query_params)
                count += response.get('Count', 0)
                
                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break
            
            return count
        except ClientError as e:
            logger.error(f"Error counting words from DynamoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error counting words: {str(e)}")
            raise

    def get_word_by_id(self, word_id: int) -> Optional[Dict]:
        """
        指定されたIDの単語を取得します
        """
        try:
            response = self.table.get_item(
                Key={
                    'PK': "WORD",
                    'SK': str(word_id)
                }
            )
            
            item = response.get('Item')
            if not item:
                raise HTTPException(status_code=404, detail="Word not found")
            
            return self._convert_dynamodb_to_model(item)
            
        except ClientError as e:
            logger.error(f"Error getting word {word_id} from DynamoDB: {str(e)}")
            raise
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting word {word_id}: {str(e)}")
            raise

    def get_kanjis_by_word_id(self, word_id: int) -> List[Dict]:
        """
        指定された単語IDに関連する漢字を取得します
        """
        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={
                    ":pk": f"WORD#{word_id}"
                }
            )
            
            items = response.get('Items', [])
            kanjis = []
            
            for item in items:
                try:
                    # SKからKANJI#を除去してIDを取得
                    kanji_id = int(item['SK'].replace('KANJI#', ''))
                    kanji = {
                        'id': kanji_id,
                        'char': item.get('kanji', '')
                    }
                    kanjis.append(kanji)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting kanji item {item['SK']}: {str(e)}")
                    continue
            
            return kanjis
            
        except ClientError as e:
            logger.error(f"Error getting kanjis for word {word_id} from DynamoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting kanjis for word {word_id}: {str(e)}")
            raise

    def _convert_dynamodb_to_model(self, item: Dict) -> Dict:
        """
        DynamoDBのアイテムをモデル形式に変換します
        """
        return {
            'id': int(item['SK']),
            'name': item.get('name', ''),
            'hiragana': item.get('hiragana', ''),
            'is_katakana': bool(int(item.get('is_katakana', 0))),
            'level': int(item.get('level', 0)),
            'english': item.get('english', ''),
            'vietnamese': item.get('vietnamese', ''),
            'chinese': item.get('chinese'),
            'korean': item.get('korean'),
            'indonesian': item.get('indonesian'),
            'hindi': item.get('hindi'),
            'lexical_category': item.get('lexical_category', ''),
            'accent_up': int(item.get('accent_up')) if item.get('accent_up') else None,
            'accent_down': int(item.get('accent_down')) if item.get('accent_down') else None
        }

dynamodb_client = DynamoDBClient() 