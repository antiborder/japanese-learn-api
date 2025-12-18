import logging
import boto3
from boto3.dynamodb.types import TypeDeserializer
from datetime import datetime, timezone
from typing import Dict, Optional, List, Union
from botocore.exceptions import ClientError
from fastapi import HTTPException
from .base import DynamoDBBase

logger = logging.getLogger(__name__)
deserializer = TypeDeserializer()

class NextDynamoDB(DynamoDBBase):
    def __init__(self):
        super().__init__()
        # batch_get_item用にclientも初期化
        self.dynamodb_client = boto3.client('dynamodb')

    async def get_word_detail(self, word_id: int) -> Optional[dict]:
        """DynamoDBから単語詳細を取得。単語が見つからない場合はNoneを返す
        ProjectionExpressionを使用してembeddingフィールドを除外し、必要なフィールドのみを取得します。
        """
        try:
            response = self.table.get_item(
                Key={
                    'PK': "WORD",
                    'SK': str(word_id)
                },
                ProjectionExpression="SK, #name, hiragana, is_katakana, #level, english, vietnamese, chinese, korean, indonesian, hindi, lexical_category, accent_up, accent_down",
                ExpressionAttributeNames={
                    "#name": "name",
                    "#level": "level"
                }
            )
            item = response.get('Item')
            if not item:
                logger.warning(f"Word {word_id} not found in DynamoDB")
                return None
            
            return {
                "id": int(item['SK']),
                "name": item.get("name", ""),
                "hiragana": item.get("hiragana", ""),
                "is_katakana": bool(int(item.get("is_katakana", 0))),
                "level": int(item.get("level", 0)),
                "english": item.get("english"),
                "vietnamese": item.get("vietnamese"),
                "chinese": item.get("chinese"),
                "korean": item.get("korean"),
                "indonesian": item.get("indonesian"),
                "hindi": item.get("hindi"),
                "lexical_category": item.get("lexical_category", ""),
                "accent_up": int(item.get("accent_up")) if item.get("accent_up") else None,
                "accent_down": int(item.get("accent_down")) if item.get("accent_down") else None
            }
        except Exception as e:
            error_msg = f"Error getting word detail for word_id {word_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None

    async def batch_get_word_details(self, word_ids: List[int]) -> Dict[int, Optional[dict]]:
        """複数の単語詳細を一度に取得します（batch_get_itemを使用）
        
        Args:
            word_ids: 取得する単語IDのリスト
            
        Returns:
            word_idをキー、単語詳細（またはNone）を値とする辞書
        """
        if not word_ids:
            return {}
        
        try:
            # DynamoDBのbatch_get_itemは最大100アイテムまで
            # 通常は4つ程度なので問題なし
            keys = [
                {
                    'PK': {"S": "WORD"},
                    'SK': {"S": str(word_id)}
                }
                for word_id in word_ids
            ]
            
            # batch_get_itemを使用（boto3.clientを使用）
            response = self.dynamodb_client.batch_get_item(
                RequestItems={
                    self.table_name: {
                        'Keys': keys,
                        'ProjectionExpression': "SK, #name, hiragana, is_katakana, #level, english, vietnamese, chinese, korean, indonesian, hindi, lexical_category, accent_up, accent_down",
                        'ExpressionAttributeNames': {
                            "#name": "name",
                            "#level": "level"
                        }
                    }
                }
            )
            
            # レスポンスをword_idをキーとする辞書に変換
            items = response.get('Responses', {}).get(self.table_name, [])
            result = {}
            
            # 取得できたアイテムを変換（DynamoDBの低レベルAPI形式から高レベル形式に変換）
            for item in items:
                # TypeDeserializerで低レベルAPI形式を高レベル形式に変換
                deserialized_item = {k: deserializer.deserialize(v) for k, v in item.items()}
                word_id = int(deserialized_item['SK'])
                result[word_id] = {
                    "id": word_id,
                    "name": deserialized_item.get("name", ""),
                    "hiragana": deserialized_item.get("hiragana", ""),
                    "is_katakana": bool(int(deserialized_item.get("is_katakana", 0))),
                    "level": int(deserialized_item.get("level", 0)),
                    "english": deserialized_item.get("english"),
                    "vietnamese": deserialized_item.get("vietnamese"),
                    "chinese": deserialized_item.get("chinese"),
                    "korean": deserialized_item.get("korean"),
                    "indonesian": deserialized_item.get("indonesian"),
                    "hindi": deserialized_item.get("hindi"),
                    "lexical_category": deserialized_item.get("lexical_category", ""),
                    "accent_up": int(deserialized_item["accent_up"]) if deserialized_item.get("accent_up") is not None else None,
                    "accent_down": int(deserialized_item["accent_down"]) if deserialized_item.get("accent_down") is not None else None
                }
            
            # 取得できなかったword_idはNoneとして設定
            for word_id in word_ids:
                if word_id not in result:
                    result[word_id] = None
            
            return result
        except Exception as e:
            logger.error(f"Error batch getting word details: {str(e)}", exc_info=True)
            # エラー時は全てNoneを返す
            return {word_id: None for word_id in word_ids}

    async def _get_level_words(self, level: int) -> List[Dict]:
        """指定されたレベルの単語を取得します（word-level-index GSIを使用）"""
        try:
            response = self.table.query(
                IndexName='word-level-index',
                KeyConditionExpression="PK = :pk AND #level = :level",
                ExpressionAttributeNames={
                    "#level": "level"
                },
                ExpressionAttributeValues={
                    ":pk": "WORD",
                    ":level": int(level)
                }
            )
            level_words = response.get('Items', [])
            if not level_words:
                logger.info(f"No words found for level {level}")
                return []
            
            logger.info(f"Successfully retrieved {len(level_words)} words for level {level}")
            return level_words
        except Exception as e:
            logger.error(f"Error getting words for level {level}: {str(e)}")
            raise

    async def _get_user_words(self, user_id: str) -> List[Dict]:
        """ユーザーの学習履歴を取得します"""
        response = self.table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
            ExpressionAttributeValues={
                ':pk': f"USER#{user_id}",
                ':sk_prefix': 'WORD#'
            }
        )
        return response.get('Items', [])

    async def _get_user_words_by_level(self, user_id: str, level: int) -> List[Dict]:
        """指定されたユーザーとレベルの学習履歴を取得します（user-level-index GSIを使用）"""
        try:
            response = self.table.query(
                IndexName='user-level-index',
                KeyConditionExpression='PK = :pk AND #level = :level',
                ExpressionAttributeNames={
                    '#level': 'level'
                },
                ExpressionAttributeValues={
                    ':pk': f"USER#{user_id}",
                    ':level': int(level)
                }
            )
            user_level_words = response.get('Items', [])
            # SKがWORD#で始まるものだけをフィルタリング（念のため）
            filtered_words = [
                item for item in user_level_words 
                if item.get('SK', '').startswith('WORD#')
            ]
            if not filtered_words:
                logger.info(f"No learning history found for user {user_id}, level {level}")
                return []
            
            logger.info(f"Successfully retrieved {len(filtered_words)} learning history items for user {user_id}, level {level}")
            return filtered_words
        except Exception as e:
            logger.error(f"Error getting user words for user {user_id}, level {level}: {str(e)}")
            raise

    async def _get_all_words(self) -> List[Dict]:
        """全単語を取得します"""
        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={
                    ":pk": "WORD"
                }
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting all words: {str(e)}")
            raise 