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

    async def get_word_detail(self, word_id: int) -> dict:
        """DynamoDBから単語詳細を取得"""
        response = self.table.get_item(
            Key={
                'PK': "WORD",
                'SK': str(word_id)
            }
        )
        item = response.get('Item')
        if not item:
            raise HTTPException(status_code=404, detail=f"Word {word_id} not found")
        return {
            "id": int(item['SK']),
            "name": item.get("name", ""),
            "hiragana": item.get("hiragana", ""),
            "is_katakana": bool(int(item.get("is_katakana", 0))),
            "level": int(item.get("level", 0)),
            "english": item.get("english", ""),
            "vietnamese": item.get("vietnamese", ""),
            "lexical_category": item.get("lexical_category", ""),
            "accent_up": int(item.get("accent_up")) if item.get("accent_up") else None,
            "accent_down": int(item.get("accent_down")) if item.get("accent_down") else None
        }

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