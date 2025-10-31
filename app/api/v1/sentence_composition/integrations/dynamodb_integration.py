import boto3
import os
import logging
import random
from datetime import datetime, timezone
from typing import List, Dict, Optional
from botocore.exceptions import ClientError
from fastapi import HTTPException
from decimal import Decimal

logger = logging.getLogger(__name__)

class DynamoDBSentenceCompositionClient:
    def __init__(self):
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.table_name)

    def get_random_sentence_by_level(self, level: int) -> Optional[Dict]:
        """
        指定されたレベルからランダムに1つの文を取得します
        """
        try:
            # 指定されたレベルの文を全て取得
            response = self.table.query(
                KeyConditionExpression="PK = :pk",
                FilterExpression="#level = :level",
                ExpressionAttributeNames={
                    "#level": "level"
                },
                ExpressionAttributeValues={
                    ":pk": "SENTENCE",
                    ":level": level
                }
            )
            
            items = response.get('Items', [])
            if not items:
                raise HTTPException(status_code=404, detail=f"No sentences found for level {level}")
            
            # ランダムに1つ選択
            random_item = random.choice(items)
            return self._convert_dynamodb_to_model(random_item)
            
        except ClientError as e:
            logger.error(f"Error getting random sentence for level {level} from DynamoDB: {str(e)}")
            raise
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting random sentence for level {level}: {str(e)}")
            raise

    def _convert_dynamodb_to_model(self, item: Dict) -> Dict:
        """
        DynamoDBのアイテムをモデル形式に変換します
        """
        from decimal import Decimal
        
        # grammar_idsの変換
        grammar_ids = []
        if 'grammar_ids' in item and item['grammar_ids']:
            for g in item['grammar_ids']:
                if isinstance(g, Decimal):
                    grammar_ids.append(int(g))
                elif isinstance(g, (int, float)):
                    grammar_ids.append(int(g))
                elif isinstance(g, dict) and 'N' in g:
                    grammar_ids.append(int(g['N']))
        
        # wordsの変換
        words = []
        if 'words' in item and item['words']:
            for word_item in item['words']:
                if isinstance(word_item, dict):
                    word_id = None
                    word_name = ''
                    
                    # word_idの処理
                    if 'word_id' in word_item and word_item['word_id'] is not None:
                        if isinstance(word_item['word_id'], (int, float, Decimal)):
                            word_id = int(word_item['word_id'])
                        elif isinstance(word_item['word_id'], dict):
                            if 'N' in word_item['word_id']:
                                word_id = int(word_item['word_id']['N'])
                    
                    # word_nameの処理
                    if 'word_name' in word_item and word_item['word_name']:
                        if isinstance(word_item['word_name'], str):
                            word_name = word_item['word_name']
                        elif isinstance(word_item['word_name'], dict) and 'S' in word_item['word_name']:
                            word_name = word_item['word_name']['S']
                    
                    words.append({
                        'word_id': word_id,
                        'word_name': word_name
                    })
        
        # dummy_wordsの変換
        dummy_words = []
        if 'dummy_words' in item and item['dummy_words']:
            for dummy_item in item['dummy_words']:
                if isinstance(dummy_item, str):
                    dummy_words.append(dummy_item)
                elif isinstance(dummy_item, dict) and 'S' in dummy_item:
                    dummy_words.append(dummy_item['S'])
        
        return {
            'sentence_id': int(item['SK']),
            'japanese': item.get('japanese', ''),
            'level': int(item.get('level', 0)),
            'hurigana': item.get('hurigana', ''),
            'english': item.get('english'),
            'vietnamese': item.get('vietnamese'),
            'chinese': item.get('chinese'),
            'korean': item.get('korean'),
            'indonesian': item.get('indonesian'),
            'hindi': item.get('hindi'),
            'grammar_ids': grammar_ids,
            'words': words,
            'dummy_words': dummy_words
        }

    def get_current_learning_data(self, user_id: str, sentence_id: int) -> Optional[Dict]:
        """現在の学習データを取得します"""
        try:
            response = self.table.get_item(
                Key={
                    'PK': f"USER#{user_id}",
                    'SK': f"SENTENCE#{sentence_id}"
                }
            )
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting learning data: {str(e)}")
            return None

    async def save_learning_data(self, 
                                user_id: str, 
                                sentence_id: int, 
                                level: int,
                                proficiency: Decimal,
                                next_datetime: datetime) -> Dict:
        """学習データをDynamoDBに保存します（DB操作のみ）"""
        try:
            # DynamoDBに保存するアイテムを作成
            item = {
                'PK': f"USER#{user_id}",
                'SK': f"SENTENCE#{sentence_id}",
                'user_id': user_id,
                'sentence_id': sentence_id,
                'level': level,
                'proficiency': proficiency,
                'next_datetime': next_datetime.isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # DynamoDBに保存
            self.table.put_item(Item=item)
            
            return {
                'user_id': user_id,
                'sentence_id': sentence_id,
                'level': level,
                'proficiency': proficiency,
                'next_datetime': next_datetime,
                'updated_at': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Error saving learning data: {str(e)}")
            raise

    async def get_user_sentences(self, user_id: str) -> List[Dict]:
        """ユーザーの学習履歴を取得します"""
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f"USER#{user_id}",
                    ':sk_prefix': 'SENTENCE#'
                }
            )
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error getting user sentences: {str(e)}")
            return []

    async def get_level_sentences(self, level: int) -> List[Dict]:
        """指定されたレベルの文を取得します"""
        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk",
                FilterExpression="#level = :level",
                ExpressionAttributeNames={
                    "#level": "level"
                },
                ExpressionAttributeValues={
                    ":pk": "SENTENCE",
                    ":level": level
                }
            )
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error getting level sentences from DynamoDB: {str(e)}")
            return []

    async def get_sentence_detail(self, sentence_id: int) -> Optional[Dict]:
        """文の詳細情報を取得します"""
        try:
            response = self.table.get_item(
                Key={
                    'PK': "SENTENCE",
                    'SK': str(sentence_id)
                }
            )
            
            item = response.get('Item')
            if not item:
                raise HTTPException(status_code=404, detail=f"Sentence {sentence_id} not found")
            
            return self._convert_dynamodb_to_model(item)
            
        except ClientError as e:
            logger.error(f"Error getting sentence {sentence_id} from DynamoDB: {str(e)}")
            raise
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting sentence {sentence_id}: {str(e)}")
            raise

dynamodb_sentence_composition_client = DynamoDBSentenceCompositionClient()
