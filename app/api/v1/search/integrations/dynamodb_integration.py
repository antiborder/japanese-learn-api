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
        language: 'zh-Hans' の場合は name と chinese を検索
        language: 'ko' の場合は name と korean を検索
        language: 'id' の場合は name と indonesian を検索
        language: 'hi' の場合は name と hindi を検索
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
                
            elif language == 'zh-Hans':
                # 中国語（簡体字）検索：name-index と chinese-index を使用
                name_results = self._search_by_name(query)
                chinese_results = self._search_by_chinese(query)
                all_results = name_results + chinese_results
                
            elif language == 'ko':
                # 韓国語検索：name-index と korean-index を使用
                name_results = self._search_by_name(query)
                korean_results = self._search_by_korean(query)
                all_results = name_results + korean_results
                
            elif language == 'id':
                # インドネシア語検索：name-index と indonesian-index を使用
                name_results = self._search_by_name(query)
                indonesian_results = self._search_by_indonesian(query)
                all_results = name_results + indonesian_results
                
            elif language == 'hi':
                # ヒンディー語検索：name-index と hindi-index を使用
                name_results = self._search_by_name(query)
                hindi_results = self._search_by_hindi(query)
                all_results = name_results + hindi_results
                
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

    def _search_by_chinese(self, query: str) -> List[Dict]:
        """
        中国語（簡体字）で検索します（chinese-index GSIを使用）
        """
        try:
            response = self.table.query(
                IndexName='chinese-index',
                KeyConditionExpression='#chinese = :chinese',
                ExpressionAttributeNames={
                    '#chinese': 'chinese'
                },
                ExpressionAttributeValues={
                    ':chinese': query
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
            logger.error(f"Error searching by chinese in DynamoDB: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error")

    def _search_by_korean(self, query: str) -> List[Dict]:
        """
        韓国語で検索します（korean-index GSIを使用）
        """
        try:
            response = self.table.query(
                IndexName='korean-index',
                KeyConditionExpression='#korean = :korean',
                ExpressionAttributeNames={
                    '#korean': 'korean'
                },
                ExpressionAttributeValues={
                    ':korean': query
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
            logger.error(f"Error searching by korean in DynamoDB: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error")

    def _search_by_indonesian(self, query: str) -> List[Dict]:
        """
        インドネシア語で検索します（indonesian-index GSIを使用）
        """
        try:
            response = self.table.query(
                IndexName='indonesian-index',
                KeyConditionExpression='#indonesian = :indonesian',
                ExpressionAttributeNames={
                    '#indonesian': 'indonesian'
                },
                ExpressionAttributeValues={
                    ':indonesian': query
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
            logger.error(f"Error searching by indonesian in DynamoDB: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error")

    def _search_by_hindi(self, query: str) -> List[Dict]:
        """
        ヒンディー語で検索します（hindi-index GSIを使用）
        """
        try:
            response = self.table.query(
                IndexName='hindi-index',
                KeyConditionExpression='#hindi = :hindi',
                ExpressionAttributeNames={
                    '#hindi': 'hindi'
                },
                ExpressionAttributeValues={
                    ':hindi': query
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
            logger.error(f"Error searching by hindi in DynamoDB: {str(e)}")
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
                
            elif language == 'zh-Hans':
                # 中国語（簡体字）検索：name-index と chinese-index を使用
                name_results = self._search_by_name(query)
                chinese_results = self._search_by_chinese(query)
                all_results = name_results + chinese_results
                
            elif language == 'ko':
                # 韓国語検索：name-index と korean-index を使用
                name_results = self._search_by_name(query)
                korean_results = self._search_by_korean(query)
                all_results = name_results + korean_results
                
            elif language == 'id':
                # インドネシア語検索：name-index と indonesian-index を使用
                name_results = self._search_by_name(query)
                indonesian_results = self._search_by_indonesian(query)
                all_results = name_results + indonesian_results
                
            elif language == 'hi':
                # ヒンディー語検索：name-index と hindi-index を使用
                name_results = self._search_by_name(query)
                hindi_results = self._search_by_hindi(query)
                all_results = name_results + hindi_results
                
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

    def search_kanjis(self, query: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        """
        漢字を検索します（character-index GSIを使用）
        """
        try:
            response = self.table.query(
                IndexName='character-index',
                KeyConditionExpression='#character = :character',
                ExpressionAttributeNames={
                    '#character': 'character'
                },
                ExpressionAttributeValues={
                    ':character': query
                }
            )
            
            items = response.get('Items', [])
            kanjis = []
            for item in items:
                try:
                    kanji = self._convert_kanji_dynamodb_to_model(item)
                    kanjis.append(kanji)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting kanji item {item.get('SK', 'unknown')}: {str(e)}")
                    continue
            
            # オフセットとリミットを適用
            start_idx = offset
            end_idx = offset + limit
            return kanjis[start_idx:end_idx]
            
        except ClientError as e:
            logger.error(f"Error searching kanjis in DynamoDB: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error")

    def get_kanji_total_count(self, query: str) -> int:
        """
        漢字検索結果の総数を取得します
        """
        try:
            response = self.table.query(
                IndexName='character-index',
                KeyConditionExpression='#character = :character',
                ExpressionAttributeNames={
                    '#character': 'character'
                },
                ExpressionAttributeValues={
                    ':character': query
                },
                Select='COUNT'
            )
            
            return response.get('Count', 0)
            
        except ClientError as e:
            logger.error(f"Error getting kanji total count from DynamoDB: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error")

    def search_components(self, query: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        """
        Componentsを検索します（character-index GSIを使用）
        """
        try:
            response = self.table.query(
                IndexName='character-index',
                KeyConditionExpression='#character = :character',
                FilterExpression='PK = :pk',
                ExpressionAttributeNames={
                    '#character': 'character'
                },
                ExpressionAttributeValues={
                    ':character': query,
                    ':pk': 'COMPONENT'
                }
            )
            
            items = response.get('Items', [])
            components = []
            for item in items:
                try:
                    component = self._convert_component_dynamodb_to_model(item)
                    components.append(component)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting component item {item.get('SK', 'unknown')}: {str(e)}")
                    continue
            
            # オフセットとリミットを適用
            start_idx = offset
            end_idx = offset + limit
            return components[start_idx:end_idx]
            
        except ClientError as e:
            logger.error(f"Error searching components in DynamoDB: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error")

    def get_component_total_count(self, query: str) -> int:
        """
        Components検索結果の総数を取得します
        """
        try:
            response = self.table.query(
                IndexName='character-index',
                KeyConditionExpression='#character = :character',
                FilterExpression='PK = :pk',
                ExpressionAttributeNames={
                    '#character': 'character'
                },
                ExpressionAttributeValues={
                    ':character': query,
                    ':pk': 'COMPONENT'
                },
                Select='COUNT'
            )
            
            return response.get('Count', 0)
            
        except ClientError as e:
            logger.error(f"Error getting component total count from DynamoDB: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error")

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
            'chinese': item.get('chinese', ''),
            'korean': item.get('korean', ''),
            'indonesian': item.get('indonesian', ''),
            'hindi': item.get('hindi', ''),
            'lexical_category': item.get('lexical_category', ''),
            'accent_up': int(item.get('accent_up')) if item.get('accent_up') else None,
            'accent_down': int(item.get('accent_down')) if item.get('accent_down') else None
        }

    def _convert_kanji_dynamodb_to_model(self, item: Dict) -> Dict:
        """
        DynamoDBの漢字アイテムをモデル形式に変換します
        """
        return {
            'id': int(item['SK']),
            'character': item.get('character', ''),
            'english': item.get('english', ''),
            'vietnamese': item.get('vietnamese', ''),
            'strokes': int(item.get('strokes', 0)) if item.get('strokes') else None,
            'onyomi': item.get('onyomi', ''),
            'kunyomi': item.get('kunyomi', ''),
            'level': int(item.get('level', 0)) if item.get('level') else None
        }

    def _convert_component_dynamodb_to_model(self, item: Dict) -> Dict:
        """
        DynamoDBのComponentsアイテムをモデル形式に変換します
        """
        return {
            'id': int(item['SK']),
            'character': item.get('character', '')
        }

search_dynamodb_client = SearchDynamoDBClient()
