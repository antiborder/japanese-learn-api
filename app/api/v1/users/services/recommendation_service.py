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
        
        base_level（または1）から順に見ていき、おすすめする場合は配列に[科目・レベル]を格納。
        配列におすすめが2つ格納されたら早期リターンでその配列を返す。
        recommendationは最大2つとする。
        
        復習単語があるものを最優先。
        順番：
        1. words level N reviewable >= 10
        2. sentences level N reviewable >= 3
        3. words level N unlearned >= 10
        4. sentences level N unlearned >= 3
        
        Returns:
            List[Dict]: レコメンドリスト（最大2件）
        """
        try:
            # ユーザー設定を取得
            user_settings = await user_settings_db.get_user_settings(user_id)
            if not user_settings:
                logger.warning(f"User settings not found for user {user_id}")
                return []
            
            base_level = user_settings.base_level if user_settings.base_level else MIN_LEVEL
            recommendations = []
            
            # base_levelから順にレベル15まで見ていく
            for level in range(base_level, min(MAX_LEVEL, 15) + 1):
                # レベルごとにwordsとsentencesのprogressを取得
                words_progress = await progress_db.get_progress_by_level(user_id, level)
                sentences_progress = await sentences_progress_db.get_progress_by_level(user_id, level)
                
                # 1-a: words level N reviewable >= 10
                if words_progress and words_progress.get('reviewable', 0) >= 10:
                    rec = {'subject': 'words', 'level': level}
                    if rec not in recommendations:
                        recommendations.append(rec)
                        if len(recommendations) >= 2:
                            return recommendations
                
                # 1-b: sentences level N reviewable >= 3
                if sentences_progress and sentences_progress.get('reviewable', 0) >= 3:
                    rec = {'subject': 'sentences', 'level': level}
                    if rec not in recommendations:
                        recommendations.append(rec)
                        if len(recommendations) >= 2:
                            return recommendations
                
                # 2-a: words level N unlearned >= 10
                # （words_progressは上で既に取得済み）
                if words_progress and words_progress.get('unlearned', 0) >= 10:
                    rec = {'subject': 'words', 'level': level}
                    if rec not in recommendations:
                        recommendations.append(rec)
                        if len(recommendations) >= 2:
                            return recommendations
                
                # 2-b: sentences level N unlearned >= 3
                # （sentences_progressは上で既に取得済み）
                if sentences_progress and sentences_progress.get('unlearned', 0) >= 3:
                    rec = {'subject': 'sentences', 'level': level}
                    if rec not in recommendations:
                        recommendations.append(rec)
                        if len(recommendations) >= 2:
                            return recommendations
            
            # ここまででおすすめが0個または1個の場合はそのまま返す
            return recommendations
                
        except Exception as e:
            logger.error(f"Error getting recommendations for user {user_id}: {str(e)}")
            return []
