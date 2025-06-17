import boto3
import os
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from botocore.exceptions import ClientError
from decimal import Decimal
import math
from fastapi import HTTPException

logger = logging.getLogger(__name__)

TIME_LIMIT = Decimal('10')
PROFICIENCY_THRESHOLD = Decimal('0.4')  # 習熟度の差の閾値
BASE_INTERVAL = 6 * 60  # 基準となる間隔（6時間を分単位で表現）

class LearnHistoryDynamoDB:
    def __init__(self):
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.table_name)

    def calculate_proficiency(self, confidence: int, time: Decimal, current_data: Optional[Dict] = None) -> Decimal:
        """習熟度を計算します"""
        easiness_point = Decimal('0.1') + (Decimal(str(confidence))/Decimal('3')) * Decimal('0.8')
        
        # 前回の学習時間との差を計算
        if current_data and 'updated_at' in current_data:
            previous_datetime = datetime.fromisoformat(current_data['updated_at'])
            current_datetime = datetime.now()
            previous_min = (current_datetime - previous_datetime).total_seconds() / 60
            interval_point = Decimal(str(max(0, min(1, math.log2(previous_min/BASE_INTERVAL) / 8))))
        else:
            interval_point = Decimal('0')

        time_point = (TIME_LIMIT - time)/TIME_LIMIT

        # 各ポイントを0-1の範囲に制限
        easiness_point = max(Decimal('0'), min(Decimal('1'), easiness_point))
        time_point = max(Decimal('0'), min(Decimal('1'), time_point))

        return Decimal('0.4') * easiness_point + Decimal('0.4') * interval_point + Decimal('0.2') * time_point

    def determine_next_mode(self, proficiency_MJ: Decimal, proficiency_JM: Decimal) -> str:
        """次の学習モードを決定します
        
        Args:
            proficiency_MJ: MJモードの習熟度（0-1）
            proficiency_JM: JMモードの習熟度（0-1）
            
        Returns:
            str: 次の学習モード（"MJ" または "JM"）
        """
        # 習熟度の差を計算
        proficiency_diff = proficiency_MJ - proficiency_JM
        
        # 差が-0.4以下の場合、MJになる確率100%
        if proficiency_diff <= -PROFICIENCY_THRESHOLD:
            return "MJ"
        
        # 差が0.4以上の場合、JMになる確率100%
        if proficiency_diff >= PROFICIENCY_THRESHOLD:
            return "JM"
        
        # その他の場合、線形に確率を計算
        # -0.4から0.4の範囲を0から1の範囲にマッピング
        jm_probability = (proficiency_diff + PROFICIENCY_THRESHOLD) / (PROFICIENCY_THRESHOLD * Decimal('2'))
        
        # 確率に基づいてモードを決定
        return "JM" if random.random() < float(jm_probability) else "MJ"

    def calculate_next_datetime(self, confidence: int, next_mode: str, proficiency_MJ: Decimal, proficiency_JM: Decimal) -> datetime:
        """次の学習時間を計算します
        
        Args:
            confidence: 自信度（0-3）
            next_mode: 次の学習モード（"MJ" または "JM"）
            proficiency_MJ: MJモードの習熟度（0-1）
            proficiency_JM: JMモードの習熟度（0-1）
            
        Returns:
            datetime: 次の学習時間
        """
        if confidence == 0:
            return datetime.now() + timedelta(minutes=5)
        
        if next_mode == "MJ":
            minutes = float(6 * 60 * 2**(8*float(proficiency_MJ)))
        else:  # JM
            minutes = float(6 * 60 * 2**(8*float(proficiency_JM)))
        
        return datetime.now() + timedelta(minutes=minutes)

    def get_current_learning_data(self, user_id: str, word_id: int) -> Optional[Dict]:
        """現在の学習データを取得します"""
        try:
            response = self.table.get_item(
                Key={
                    'PK': f"USER#{user_id}",
                    'SK': f"WORD#{word_id}"
                }
            )
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting learning data: {str(e)}")
            return None

    async def record_learning(self, 
                            user_id: str, 
                            word_id: int, 
                            level: int,
                            confidence: int,
                            time: Decimal) -> Dict:
        """学習履歴を記録します"""
        try:
            # ユーザーIDがない場合は記録をスキップ
            if not user_id:
                logger.info("User ID is null or empty. Skipping DynamoDB record.")
                return {
                    'user_id': user_id,
                    'word_id': word_id,
                    'level': level,
                    'proficiency_MJ': Decimal('0'),
                    'proficiency_JM': Decimal('0'),
                    'next_mode': "MJ",  # デフォルトモード
                    'next_datetime': datetime.now() + timedelta(minutes=5)  # デフォルトの次回学習時間
                }

            # 現在のデータを取得
            current_data = self.get_current_learning_data(user_id, word_id)
                        
            # 現在のデータがある場合は更新、ない場合は新規作成
            if current_data:
                proficiency_MJ = Decimal(str(current_data.get('proficiency_MJ', '0')))
                proficiency_JM = Decimal(str(current_data.get('proficiency_JM', '0')))
            else:
                proficiency_MJ = Decimal('0')
                proficiency_JM = Decimal('0')
            
            # 次の学習モードを決定
            next_mode = self.determine_next_mode(proficiency_MJ, proficiency_JM)

            # 習熟度を計算
            new_proficiency = self.calculate_proficiency(confidence, time, current_data)            
            
            # 新しい習熟度を更新
            if next_mode == "MJ":
                proficiency_MJ = new_proficiency
            else:
                proficiency_JM = new_proficiency
            
            # 次の学習時間を計算
            next_datetime = self.calculate_next_datetime(confidence, next_mode, proficiency_MJ, proficiency_JM)

            # DynamoDBに保存するアイテムを作成
            item = {
                'PK': f"USER#{user_id}",
                'SK': f"WORD#{word_id}",
                'user_id': user_id,
                'word_id': word_id,
                'level': level,
                'proficiency_MJ': proficiency_MJ,
                'proficiency_JM': proficiency_JM,
                'next_mode': next_mode,
                'next_datetime': next_datetime.isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # DynamoDBに保存
            self.table.put_item(Item=item)
            
            return {
                'user_id': user_id,
                'word_id': word_id,
                'level': level,
                'proficiency_MJ': proficiency_MJ,
                'proficiency_JM': proficiency_JM,
                'next_mode': next_mode,
                'next_datetime': next_datetime
            }
            
        except Exception as e:
            logger.error(f"Error recording learning data: {str(e)}")
            raise

    async def get_next_word(self, user_id: str, level: int) -> Optional[Dict]:
        """次に学習すべき単語を取得します"""
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
            # レベルでフィルタリング
            level_words = [item for item in all_words if item.get('level') == level]
            if not level_words:
                logger.info(f"No words found for level {level}")
                return None
            # ②user_idがnullの場合はランダム選択
            if not user_id:
                selected_item = random.choice(level_words)
                result = {
                    'answer_word_id': int(selected_item['SK']),
                    'mode': random.choice(["MJ", "JM"])
                }
                logger.info(f"Successfully retrieved random word for level {level}: {result}")
                return result
            # ③ユーザーの学習履歴の取得とレベルでのフィルタリング
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f"USER#{user_id}",
                    ':sk_prefix': 'WORD#'
                }
            )
            user_words = response.get('Items', [])
            user_level_words = [item for item in user_words if item.get('level') == level]
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
                    logger.info(f"Successfully retrieved new word for user {user_id}, level {level}: {result}")
                    return result
            # review_selection: next_timeが最も若い単語を選択
            if user_level_words:
                answer_word = min(user_level_words, key=lambda x: x['next_datetime'])
                result = {
                    'answer_word_id': answer_word['word_id'],
                    'mode': answer_word['next_mode']
                }
                logger.info(f"Successfully retrieved review word for user {user_id}, level {level}: {result}")
                return result
            # ユーザーの学習履歴に単語がない場合は、ランダムに選択
            selected_item = random.choice(level_words)
            result = {
                'answer_word_id': int(selected_item['SK']),
                'mode': random.choice(["MJ", "JM"])
            }
            logger.info(f"Successfully retrieved random word for user {user_id}, level {level}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error getting next word for user {user_id}, level {level}: {str(e)}", exc_info=True)
            raise

    async def get_other_words(self, level: int, exclude_id: int) -> List[int]:
        """指定されたレベルで、除外ID以外の単語を3つ取得します"""
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
            # レベルでフィルタリングし、除外IDを除く
            filtered_items = [
                item for item in items 
                if item.get('level') == level and int(item['SK']) != exclude_id
            ]
            if len(filtered_items) < 3:
                logger.info(f"Not enough words found for level {level} excluding word {exclude_id}")
                return []
            # ランダムに3つ選択
            selected_items = random.sample(filtered_items, 3)
            # word_idのリストを返す
            word_ids = [int(item['SK']) for item in selected_items]
            logger.info(f"Successfully retrieved 3 other words for level {level}, excluding word {exclude_id}")
            return word_ids
        except Exception as e:
            logger.error(f"Error getting other words for level {level}, excluding word {exclude_id}: {str(e)}", exc_info=True)
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

learn_history_db = LearnHistoryDynamoDB() 