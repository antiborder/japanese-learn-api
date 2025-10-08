import logging
import random
from typing import Dict, List, Optional
from .datetime_utils import DateTimeUtils

logger = logging.getLogger(__name__)

class SentenceSelector:
    @staticmethod
    def select_new_sentence(level_sentences: List[Dict], user_sentences: List[Dict]) -> Optional[Dict]:
        """新しい文を選択します"""
        # ユーザーが学習済みの文IDを取得
        user_learned_ids = [int(s['sentence_id']) for s in user_sentences]
        
        # 新しい文（学習済みでない文）をフィルタリング
        new_sentences = [
            sentence for sentence in level_sentences 
            if int(sentence['SK']) not in user_learned_ids
        ]
        
        if not new_sentences:
            return None
        
        # ランダムに選択
        selected_item = random.choice(new_sentences)
        return {
            'answer_sentence_id': int(selected_item['SK'])
        }
    
    @staticmethod
    def select_review_sentence(user_level_sentences: List[Dict]) -> Optional[Dict]:
        """復習文を選択します"""
        if not user_level_sentences:
            return None
        
        # 復習可能な文をフィルタリング
        reviewable_sentences = []
        for sentence in user_level_sentences:
            if DateTimeUtils.is_reviewable(sentence):
                reviewable_sentences.append(sentence)
        
        if not reviewable_sentences:
            return None
        
        # next_datetimeが最も古いものを選択
        answer_sentence = min(reviewable_sentences, key=lambda x: x['next_datetime'])
        return {
            'answer_sentence_id': answer_sentence['sentence_id']
        }
    
    @staticmethod
    def select_next_sentence(level_sentences: List[Dict], user_sentences: List[Dict], 
                           user_id: str, level: int) -> Optional[Dict]:
        """次に学習すべき文を選択します"""
        user_level_sentences = [item for item in user_sentences if item.get('level') == level]
        
        # ratioベースでの選定
        ratio = len(user_level_sentences) / len(level_sentences) if level_sentences else 0
        if random.random() > ratio:
            # random_selection: 新しい文を選択
            new_sentence_result = SentenceSelector.select_new_sentence(level_sentences, user_level_sentences)
            if new_sentence_result:
                logger.info(f"Successfully retrieved new sentence for user {user_id}, level {level}: {new_sentence_result}")
                return new_sentence_result
        
        # review_selection: 復習文を選択
        review_sentence_result = SentenceSelector.select_review_sentence(user_level_sentences)
        if review_sentence_result:
            logger.info(f"Successfully retrieved review sentence for user {user_id}, level {level}: {review_sentence_result}")
            return review_sentence_result
        
        # 復習可能な文がない場合は、次に利用可能になる時刻を計算
        next_available_dt = DateTimeUtils.get_next_available_time(user_level_sentences)
        if next_available_dt:
            result = {
                'no_sentence_available': True,
                'next_available_datetime': next_available_dt
            }
            logger.info(f"No reviewable sentences available for user {user_id}, level {level}. Next available at: {next_available_dt}")
            return result
        
        # ユーザーの学習履歴に文がない場合は、ランダムに選択
        if level_sentences:
            selected_item = random.choice(level_sentences)
            random_result = {
                'answer_sentence_id': int(selected_item['SK'])
            }
            logger.info(f"Successfully retrieved random sentence for user {user_id}, level {level}: {random_result}")
            return random_result
        
        return None
