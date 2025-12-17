import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List, Union
from botocore.exceptions import ClientError
from fastapi import HTTPException
from .base import DynamoDBBase

logger = logging.getLogger(__name__)

class NextDynamoDB(DynamoDBBase):
    def __init__(self):
        super().__init__()

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