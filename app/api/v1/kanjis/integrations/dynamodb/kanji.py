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

    def get_kanjis(self, skip: int = 0, limit: int = 100):
        """
        漢字情報を取得します（skip/limit対応）
        
        Args:
            skip: スキップする件数
            limit: 取得する最大件数
        """
        try:
            # すべての漢字を取得（DynamoDBのqueryはページネーションが必要な場合がある）
            all_items = []
            last_evaluated_key = None
            
            while True:
                query_params = {
                    "KeyConditionExpression": "PK = :pk",
                    "ExpressionAttributeValues": {
                        ":pk": "KANJI"
                    }
                }
                
                if last_evaluated_key:
                    query_params["ExclusiveStartKey"] = last_evaluated_key
                
                response = self.table.query(**query_params)
                items = response.get('Items', [])
                all_items.extend(items)
                
                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break
            
            # 各アイテムにidフィールドを追加
            for item in all_items:
                kanji_id = int(item['SK'])
                item['id'] = kanji_id
            
            # skip/limitを適用
            return all_items[skip:skip + limit]
        except Exception as e:
            logger.error(f"Error getting kanjis from DynamoDB: {str(e)}")
            raise

    def count_kanjis(self) -> int:
        """
        漢字の総件数を取得します
        """
        try:
            count = 0
            last_evaluated_key = None
            
            while True:
                query_params = {
                    "KeyConditionExpression": "PK = :pk",
                    "ExpressionAttributeValues": {
                        ":pk": "KANJI"
                    },
                    "Select": "COUNT"
                }
                
                if last_evaluated_key:
                    query_params["ExclusiveStartKey"] = last_evaluated_key
                
                response = self.table.query(**query_params)
                count += response.get('Count', 0)
                
                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break
            
            return count
        except Exception as e:
            logger.error(f"Error counting kanjis from DynamoDB: {str(e)}")
            raise

    def get_components_by_kanji_id(self, kanji_id: str):
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f'KANJI#{kanji_id}'
                }
            )
            items = response.get('Items', [])
            result = []
            for item in items:
                # SKは "COMPONENT#{component_id}" 形式
                component_id = item['SK'].replace('COMPONENT#', '')
                component_char = item.get('component_char')
                result.append({
                    'component_id': component_id,
                    'component_char': component_char
                })
            return result
        except Exception as e:
            logger.error(f"Error getting components for kanji {kanji_id} from DynamoDB: {str(e)}")
            raise

    def get_words_by_kanji_id(self, kanji_id: int):
        """
        指定された漢字IDに関連する単語を取得します
        """
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f'KANJI#{kanji_id}'
                }
            )
            
            items = response.get('Items', [])
            words = []
            
            for item in items:
                try:
                    # SKからWORD#を除去してIDを取得
                    word_id = int(item['SK'].replace('WORD#', ''))
                    word = {
                        'id': word_id
                    }
                    words.append(word)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting word item {item['SK']}: {str(e)}")
                    continue
            
            return words
            
        except Exception as e:
            logger.error(f"Error getting words for kanji {kanji_id} from DynamoDB: {str(e)}")
            raise

dynamodb_kanji_client = DynamoDBKanjiClient() 