import logging
from typing import List, Dict, Optional
from integrations.dynamodb import progress_db, sentences_progress_db, user_settings_db
from common.config import MIN_LEVEL, MAX_LEVEL

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self):
        pass
    
    async def get_recommendations(self, user_id: str) -> List[Dict]:
        """
        ユーザーのレコメンドを取得する
        
        Returns:
            List[Dict]: レコメンドリスト（最大2件）
        """
        try:
            # ユーザー設定を取得
            user_settings = await user_settings_db.get_user_settings(user_id)
            if not user_settings:
                logger.warning(f"User settings not found for user {user_id}")
                return []
            
            base_level = user_settings.base_level
            recommendations = []
            
            # ユーザーの学習履歴を一度だけ取得（再利用のため）
            words_user_items = await self._get_user_words_items(user_id)
            sentences_user_items = await self._get_user_sentences_items(user_id)
            
            # レベルごとのprogressデータをキャッシュ（ステップ2で再利用）
            words_progress_cache = {}
            sentences_progress_cache = {}
            
            # ステップ1: 復習単語があるものを最優先（レベル1-15まで順に見ていく）
            for level in range(base_level, min(16, MAX_LEVEL + 1)):  # レベル15まで
                if len(recommendations) >= 2:
                    return recommendations
                
                # 1-a: words level reviewable >= 10 なら、words level をおすすめ
                words_progress = await progress_db.get_progress_by_level(
                    user_id, level, words_user_items
                )
                words_progress_cache[level] = words_progress
                if words_progress and words_progress.get('reviewable', 0) >= 10:
                    recommendations.append({'subject': 'words', 'level': level})
                    if len(recommendations) >= 2:
                        return recommendations
                
                # 1-b: sentences level reviewable >= 3 なら、sentences level をおすすめ
                sentences_progress = await sentences_progress_db.get_progress_by_level(
                    user_id, level, sentences_user_items
                )
                sentences_progress_cache[level] = sentences_progress
                if sentences_progress and sentences_progress.get('reviewable', 0) >= 3:
                    recommendations.append({'subject': 'sentences', 'level': level})
                    if len(recommendations) >= 2:
                        return recommendations
            
            # ここまででおすすめが1つだけなら、それを返す
            if len(recommendations) == 1:
                return recommendations
            
            # ステップ2: 未習単語があるものを次に優先（レベル1-15まで順に見ていく）
            for level in range(base_level, min(16, MAX_LEVEL + 1)):  # レベル15まで
                if len(recommendations) >= 2:
                    return recommendations
                
                # 2-a: words level unlearned >= 10 なら、words level をおすすめ
                # (ステップ1で取得済みのデータを再利用)
                words_progress = words_progress_cache.get(level)
                if words_progress and words_progress.get('unlearned', 0) >= 10:
                    recommendations.append({'subject': 'words', 'level': level})
                    if len(recommendations) >= 2:
                        return recommendations
                
                # 2-b: sentences level unlearned >= 3 なら、sentences level をおすすめ
                # (ステップ1で取得済みのデータを再利用)
                sentences_progress = sentences_progress_cache.get(level)
                if sentences_progress and sentences_progress.get('unlearned', 0) >= 3:
                    recommendations.append({'subject': 'sentences', 'level': level})
                    if len(recommendations) >= 2:
                        return recommendations
            
            # ここまででおすすめがあれば返す（0件または1件）
            return recommendations
                
        except Exception as e:
            logger.error(f"Error getting recommendations for user {user_id}: {str(e)}")
            return []
    
    async def _get_user_words_items(self, user_id: str) -> List[Dict]:
        """ユーザーの単語学習履歴を取得"""
        try:
            user_response = progress_db.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f"USER#{user_id}",
                    ':sk_prefix': 'WORD#'
                }
            )
            return user_response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting user words items: {str(e)}")
            return []
    
    async def _get_user_sentences_items(self, user_id: str) -> List[Dict]:
        """ユーザーの例文学習履歴を取得"""
        try:
            user_response = sentences_progress_db.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f"USER#{user_id}",
                    ':sk_prefix': 'SENTENCE#'
                }
            )
            return user_response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting user sentences items: {str(e)}")
            return []
