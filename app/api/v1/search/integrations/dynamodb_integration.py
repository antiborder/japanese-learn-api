import boto3
import os
import logging
from typing import List, Dict, Optional
from botocore.exceptions import ClientError
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class SearchDynamoDBClient:
    def __init__(self):
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.table_name)

    def search_words(self, query: str, language: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        """
        単語を検索します（GSIを使用）
        language: 'en' の場合は name と english を検索
        language: 'vi' の場合は name と vietnamese を検索
        """
        try:
            all_results = []
            
            if language == 'en':
                # 英語検索：name-index と english-index を使用
                name_results = self._search_by_name(query)
                english_results = self._search_by_english(query)
                all_results = name_results + english_results
                
            elif language == 'vi':
                # ベトナム語検索：name-index と vietnamese-index を使用
                name_results = self._search_by_name(query)
                vietnamese_results = self._search_by_vietnamese(query)
                all_results = name_results + vietnamese_results
                
            else:
                raise HTTPException(status_code=400, detail="Unsupported language")
            
            # 重複を除去（同じ単語IDの場合は1つだけ残す）
            unique_results = {}
            for word in all_results:
                word_id = word['id']
                if word_id not in unique_results:
                    unique_results[word_id] = word
            
            # 結果をリストに変換
            words = list(unique_results.values())
            
            # オフセットとリミットを適用
            start_idx = offset
            end_idx = offset + limit
            return words[start_idx:end_idx]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error searching words: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    def _search_by_name(self, query: str) -> List[Dict]:
        """
        単語名で検索します（name-index GSIを使用）
        """
        try:
            response = self.table.query(
                IndexName='name-index',
                KeyConditionExpression='#name = :name',
                ExpressionAttributeNames={
                    '#name': 'name'
                },
                ExpressionAttributeValues={
                    ':name': query
                }
            )
            
            items = response.get('Items', [])
            words = []
            for item in items:
                try:
                    word = self._convert_dynamodb_to_model(item)
                    words.append(word)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting item {item.get('SK', 'unknown')}: {str(e)}")
                    continue
            
            return words
            
        except ClientError as e:
            logger.error(f"Error searching by name in DynamoDB: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error")

    def _search_by_english(self, query: str) -> List[Dict]:
        """
        英語で検索します（english-index GSIを使用）
        """
        try:
            response = self.table.query(
                IndexName='english-index',
                KeyConditionExpression='#english = :english',
                ExpressionAttributeNames={
                    '#english': 'english'
                },
                ExpressionAttributeValues={
                    ':english': query
                }
            )
            
            items = response.get('Items', [])
            words = []
            for item in items:
                try:
                    word = self._convert_dynamodb_to_model(item)
                    words.append(word)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting item {item.get('SK', 'unknown')}: {str(e)}")
                    continue
            
            return words
            
        except ClientError as e:
            logger.error(f"Error searching by english in DynamoDB: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error")

    def _search_by_vietnamese(self, query: str) -> List[Dict]:
        """
        ベトナム語で検索します（vietnamese-index GSIを使用）
        """
        try:
            response = self.table.query(
                IndexName='vietnamese-index',
                KeyConditionExpression='#vietnamese = :vietnamese',
                ExpressionAttributeNames={
                    '#vietnamese': 'vietnamese'
                },
                ExpressionAttributeValues={
                    ':vietnamese': query
                }
            )
            
            items = response.get('Items', [])
            words = []
            for item in items:
                try:
                    word = self._convert_dynamodb_to_model(item)
                    words.append(word)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting item {item.get('SK', 'unknown')}: {str(e)}")
                    continue
            
            return words
            
        except ClientError as e:
            logger.error(f"Error searching by vietnamese in DynamoDB: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error")

    def get_total_count(self, query: str, language: str) -> int:
        """
        検索結果の総数を取得します（GSIを使用）
        """
        try:
            all_results = []
            
            if language == 'en':
                # 英語検索：name-index と english-index を使用
                name_results = self._search_by_name(query)
                english_results = self._search_by_english(query)
                all_results = name_results + english_results
                
            elif language == 'vi':
                # ベトナム語検索：name-index と vietnamese-index を使用
                name_results = self._search_by_name(query)
                vietnamese_results = self._search_by_vietnamese(query)
                all_results = name_results + vietnamese_results
                
            else:
                raise HTTPException(status_code=400, detail="Unsupported language")
            
            # 重複を除去（同じ単語IDの場合は1つだけ残す）
            unique_results = {}
            for word in all_results:
                word_id = word['id']
                if word_id not in unique_results:
                    unique_results[word_id] = word
            
            return len(unique_results)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting total count: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

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
            'lexical_category': item.get('lexical_category', ''),
            'accent_up': int(item.get('accent_up')) if item.get('accent_up') else None,
            'accent_down': int(item.get('accent_down')) if item.get('accent_down') else None
        }

search_dynamodb_client = SearchDynamoDBClient()
