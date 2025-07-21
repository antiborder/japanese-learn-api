import logging
import random
from datetime import datetime, timezone
from typing import Dict, Optional, List, Union
from botocore.exceptions import ClientError
from fastapi import HTTPException
from .base import DynamoDBBase

logger = logging.getLogger(__name__)

class NextDynamoDB(DynamoDBBase):
    async def get_random_word(self, level: int) -> Optional[Dict]:
        """指定されたレベルからランダムに単語IDとモードを取得します"""
        try:
            # ①単語リストの取得とレベルでのフィルタリング
            response = self.table.query(
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={
                    ":pk": "WORD"
                }
            )
            all_words = response.get('Items', [])
            if not all_words:
                logger.info("No words found in the database")
                return None
            
            level_words = [item for item in all_words if item.get('level') == level]
            if not level_words:
                logger.info(f"No words found for level {level}")
                return None

            # ②ランダムに単語を選択
            selected_item = random.choice(level_words)
            result = {
                'answer_word_id': int(selected_item['SK']),
                'mode': random.choice(["MJ", "JM"])
            }
            logger.info(f"Successfully retrieved random word for level {level}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error getting random word for level {level}: {str(e)}", exc_info=True)
            raise

    async def get_next_word(self, user_id: str, level: Union[int, str]) -> Optional[Dict]:
        """次に学習すべき単語を取得します"""
        try:
            # REVIEW_ALLの場合の特別処理
            if level == "REVIEW_ALL":
                return await self._get_next_word_review_all(user_id)
            
            # 通常のレベル指定の場合
            level_int = int(level)
            
            # ①単語リストの取得とレベルでのフィルタリング
            response = self.table.query(
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={
                    ":pk": "WORD"
                }
            )
            all_words = response.get('Items', [])
            if not all_words:
                logger.info("No words found in the database")
                return None
            # レベルでフィルタリング
            level_words = [item for item in all_words if item.get('level') == level_int]
            if not level_words:
                logger.info(f"No words found for level {level_int}")
                return None
            
            # ③ユーザーの学習履歴の取得とレベルでのフィルタリング
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f"USER#{user_id}",
                    ':sk_prefix': 'WORD#'
                }
            )
            user_words = response.get('Items', [])
            user_level_words = [item for item in user_words if item.get('level') == level_int]
            
            # ④単語選定方法の決定
            ratio = len(user_level_words) / len(level_words)
            if random.random() > ratio:
                # random_selection: リスト①に含まれ、かつリスト③に含まれない単語をランダムに選択
                new_words = [
                    word for word in level_words 
                    if int(word['SK']) not in [int(w['word_id']) for w in user_level_words]
                ]
                if new_words:  # 新しい単語が存在する場合
                    selected_item = random.choice(new_words)
                    result = {
                        'answer_word_id': int(selected_item['SK']),
                        'mode': random.choice(["MJ", "JM"])
                    }
                    logger.info(f"Successfully retrieved new word for user {user_id}, level {level_int}: {result}")
                    return result
            
            # review_selection: next_timeが最も若い単語を選択
            if user_level_words:
                # 現在時刻を取得
                now = datetime.now(timezone.utc)
                
                # 復習可能な単語（next_datetimeが現在時刻以前）をフィルタリング
                reviewable_words = []
                for word in user_level_words:
                    try:
                        next_dt = datetime.fromisoformat(word['next_datetime'])
                        if next_dt.tzinfo is None:
                            next_dt = next_dt.replace(tzinfo=timezone.utc)
                        if next_dt <= now:
                            reviewable_words.append(word)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid next_datetime format for word {word.get('word_id')}: {e}")
                        continue
                
                if reviewable_words:
                    # 復習可能な単語がある場合は、next_datetimeが最も古いものを選択
                    answer_word = min(reviewable_words, key=lambda x: x['next_datetime'])
                    result = {
                        'answer_word_id': answer_word['word_id'],
                        'mode': answer_word['next_mode']
                    }
                    logger.info(f"Successfully retrieved review word for user {user_id}, level {level_int}: {result}")
                    return result
                else:
                    # 復習可能な単語がない場合は、次に利用可能になる時刻を計算
                    next_available_word = min(user_level_words, key=lambda x: x['next_datetime'])
                    try:
                        next_available_dt = datetime.fromisoformat(next_available_word['next_datetime'])
                        if next_available_dt.tzinfo is None:
                            next_available_dt = next_available_dt.replace(tzinfo=timezone.utc)
                        result = {
                            'no_word_available': True,
                            'next_available_datetime': next_available_dt
                        }
                        logger.info(f"No reviewable words available for user {user_id}, level {level_int}. Next available at: {next_available_dt}")
                        return result
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid next_datetime format for next available word: {e}")
                        # 日時解析に失敗した場合は、新しい単語を選択
                        pass
            
            # ユーザーの学習履歴に単語がない場合は、ランダムに選択
            selected_item = random.choice(level_words)
            result = {
                'answer_word_id': int(selected_item['SK']),
                'mode': random.choice(["MJ", "JM"])
            }
            logger.info(f"Successfully retrieved random word for user {user_id}, level {level_int}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error getting next word for user {user_id}, level {level}: {str(e)}", exc_info=True)
            raise

    async def _get_next_word_review_all(self, user_id: str) -> Optional[Dict]:
        """全レベルから復習可能な単語を取得します（next_datetimeが最も古いものを選択）"""
        try:
            # ユーザーの学習履歴を全て取得
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f"USER#{user_id}",
                    ':sk_prefix': 'WORD#'
                }
            )
            user_words = response.get('Items', [])
            if not user_words:
                logger.info(f"No learning history found for user {user_id}")
                return None
            
            # 現在時刻を取得
            now = datetime.now(timezone.utc)
            
            # 復習可能な単語（next_datetimeが現在時刻以前）をフィルタリング
            reviewable_words = []
            for word in user_words:
                try:
                    next_dt = datetime.fromisoformat(word['next_datetime'])
                    if next_dt.tzinfo is None:
                        next_dt = next_dt.replace(tzinfo=timezone.utc)
                    if next_dt <= now:
                        reviewable_words.append(word)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid next_datetime format for word {word.get('word_id')}: {e}")
                    continue
            
            if reviewable_words:
                # 復習可能な単語がある場合は、next_datetimeが最も古いものを選択
                answer_word = min(reviewable_words, key=lambda x: x['next_datetime'])
                result = {
                    'answer_word_id': answer_word['word_id'],
                    'mode': answer_word['next_mode']
                }
                logger.info(f"Successfully retrieved all-review word for user {user_id}: {result}")
                return result
            else:
                # 復習可能な単語がない場合は、次に利用可能になる時刻を計算
                next_available_word = min(user_words, key=lambda x: x['next_datetime'])
                try:
                    next_available_dt = datetime.fromisoformat(next_available_word['next_datetime'])
                    if next_available_dt.tzinfo is None:
                        next_available_dt = next_available_dt.replace(tzinfo=timezone.utc)
                    result = {
                        'no_word_available': True,
                        'next_available_datetime': next_available_dt
                    }
                    logger.info(f"No reviewable words available for user {user_id} in all levels. Next available at: {next_available_dt}")
                    return result
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid next_datetime format for next available word: {e}")
                    return None
        except Exception as e:
            logger.error(f"Error getting all-review word for user {user_id}: {str(e)}", exc_info=True)
            raise

    async def get_other_words(self, level: Union[int, str], exclude_id: int) -> List[int]:
        """指定されたレベルで、除外ID以外の単語を3つ取得します"""
        try:
            # ALL_REVIEWの場合の特別処理
            if level == "REVIEW_ALL":
                return await self._get_other_words_review_all(exclude_id)
            
            # 通常のレベル指定の場合
            level_int = int(level)
            
            response = self.table.query(
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={
                    ":pk": "WORD"
                }
            )
            items = response.get('Items', [])
            if not items:
                logger.info(f"No words found in the database")
                return []
            # レベルでフィルタリングし、除外IDを除く
            filtered_items = [
                item for item in items 
                if item.get('level') == level_int and int(item['SK']) != exclude_id
            ]
            if len(filtered_items) < 3:
                logger.info(f"Not enough words found for level {level_int} excluding word {exclude_id}")
                return []
            # ランダムに3つ選択
            selected_items = random.sample(filtered_items, 3)
            # word_idのリストを返す
            word_ids = [int(item['SK']) for item in selected_items]
            logger.info(f"Successfully retrieved 3 other words for level {level_int}, excluding word {exclude_id}")
            return word_ids
        except Exception as e:
            logger.error(f"Error getting other words for level {level}, excluding word {exclude_id}: {str(e)}", exc_info=True)
            raise

    async def _get_other_words_review_all(self, exclude_id: int) -> List[int]:
        """全レベルから除外ID以外の単語を3つ取得します"""
        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={
                    ":pk": "WORD"
                }
            )
            items = response.get('Items', [])
            if not items:
                logger.info(f"No words found in the database")
                return []
            
            # 除外IDを除く
            filtered_items = [
                item for item in items 
                if int(item['SK']) != exclude_id
            ]
            if len(filtered_items) < 3:
                logger.info(f"Not enough words found excluding word {exclude_id}")
                return []
            
            # ランダムに3つ選択
            selected_items = random.sample(filtered_items, 3)
            # word_idのリストを返す
            word_ids = [int(item['SK']) for item in selected_items]
            logger.info(f"Successfully retrieved 3 other words from all levels, excluding word {exclude_id}")
            return word_ids
        except Exception as e:
            logger.error(f"Error getting other words from all levels, excluding word {exclude_id}: {str(e)}", exc_info=True)
            raise

    async def get_word_detail(self, word_id: int) -> dict:
        """
        DynamoDBから単語詳細を取得
        """
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