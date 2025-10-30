import boto3
import os
import logging
from typing import List, Dict, Optional
from botocore.exceptions import ClientError
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class DynamoDBSentenceClient:
    def __init__(self):
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.table_name)

    def get_sentences(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={
                    ":pk": "SENTENCE"
                },
                Limit=limit
            )
            items = response.get('Items', [])
            sentences = []
            for item in items:
                try:
                    sentence = self._convert_dynamodb_to_model(item)
                    sentences.append(sentence)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting sentence item {item['SK']}: {str(e)}")
                    continue
            return sentences[skip:skip + limit]
        except ClientError as e:
            logger.error(f"Error getting sentences from DynamoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

    def get_sentence_by_id(self, sentence_id: int) -> Optional[Dict]:
        """
        指定されたIDの文を取得します
        """
        try:
            response = self.table.get_item(
                Key={
                    'PK': "SENTENCE",
                    'SK': str(sentence_id)
                }
            )
            
            item = response.get('Item')
            if not item:
                raise HTTPException(status_code=404, detail="Sentence not found")
            
            return self._convert_dynamodb_to_model(item)
            
        except ClientError as e:
            logger.error(f"Error getting sentence {sentence_id} from DynamoDB: {str(e)}")
            raise
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting sentence {sentence_id}: {str(e)}")
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
            'hurigana': item.get('hurigana', ''),  # huriganaフィールドを追加
            'english': item.get('english', ''),
            'vietnamese': item.get('vietnamese', ''),
            'chinese': item.get('chinese'),
            'korean': item.get('korean'),
            'indonesian': item.get('indonesian'),
            'hindi': item.get('hindi'),
            'grammar_ids': grammar_ids,
            'words': words,
            'dummy_words': dummy_words
        }

dynamodb_sentence_client = DynamoDBSentenceClient()
