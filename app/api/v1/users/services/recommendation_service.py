import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone
from integrations.dynamodb import progress_db, sentences_progress_db, user_settings_db
from services.datetime_utils import DateTimeUtils
from common.config import MIN_LEVEL, MAX_LEVEL

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self):
        self.datetime_utils = DateTimeUtils()
    
    async def get_recommendations(self, user_id: str) -> List[Dict]:
        """
        ユーザーのレコメンドを取得する
        
        Returns:
            List[Dict]: レコメンドリスト（最大3件）
        """
        try:
            # ユーザー設定を取得
            user_settings = await user_settings_db.get_user_settings(user_id)
            if not user_settings:
                logger.warning(f"User settings not found for user {user_id}")
                return []
            
            base_level = user_settings.base_level
            
            # 単語と例文の進捗を取得
            words_progress = await progress_db.get_progress(user_id)
            sentences_progress = await sentences_progress_db.get_progress(user_id)
            
            # learnableの総数を計算
            total_learnable = self._calculate_total_learnable(words_progress, sentences_progress)
            
            # 着手済みの科目・レベルを取得
            started_subjects = self._get_started_subjects(words_progress, sentences_progress, base_level)
            
            # レコメンドロジックを実行
            if total_learnable >= 100:
                return self._recommend_by_ratio(words_progress, sentences_progress, base_level, total_learnable)
            elif total_learnable >= 21:
                return self._recommend_mixed(words_progress, sentences_progress, base_level, started_subjects, total_learnable)
            else:
                return self._recommend_low_learnable(words_progress, sentences_progress, base_level, started_subjects, total_learnable)
                
        except Exception as e:
            logger.error(f"Error getting recommendations for user {user_id}: {str(e)}")
            return []
    
    def _calculate_total_learnable(self, words_progress: List[Dict], sentences_progress: List[Dict]) -> int:
        """learnableの総数を計算"""
        total = 0
        
        # 単語のlearnableを計算
        for progress in words_progress:
            if progress.get('reviewable', 0) > 0:
                total += progress['reviewable']
        
        # 例文のlearnableを計算
        for progress in sentences_progress:
            if progress.get('reviewable', 0) > 0:
                total += progress['reviewable']
        
        return total
    
    def _get_started_subjects(self, words_progress: List[Dict], sentences_progress: List[Dict], base_level: int) -> List[Tuple[str, int]]:
        """着手済みの科目・レベルを取得"""
        started = []
        
        # 単語の着手済みレベルを取得
        for progress in words_progress:
            level = progress.get('level', 0)
            if level >= base_level and progress.get('learned', 0) > 0:
                started.append(('words', level))
        
        # 例文の着手済みレベルを取得
        for progress in sentences_progress:
            level = progress.get('level', 0)
            if level >= base_level and progress.get('learned', 0) > 0:
                started.append(('sentences', level))
        
        return started
    
    def _recommend_by_ratio(self, words_progress: List[Dict], sentences_progress: List[Dict], base_level: int, total_learnable: int) -> List[Dict]:
        """learnableが100以上の場合のレコメンド"""
        subject_ratios = []
        
        # 各レベル・科目のlearnable割合を計算
        for level in range(base_level, MAX_LEVEL + 1):
            # 単語の割合を計算
            words_data = next((p for p in words_progress if p.get('level') == level), None)
            if words_data and words_data.get('reviewable', 0) > 0:
                ratio = words_data['reviewable'] / total_learnable if total_learnable > 0 else 0
                subject_ratios.append({
                    'subject': 'words',
                    'level': level,
                    'ratio': ratio
                })
            
            # 例文の割合を計算
            sentences_data = next((p for p in sentences_progress if p.get('level') == level), None)
            if sentences_data and sentences_data.get('reviewable', 0) > 0:
                ratio = sentences_data['reviewable'] / total_learnable if total_learnable > 0 else 0
                subject_ratios.append({
                    'subject': 'sentences',
                    'level': level,
                    'ratio': ratio
                })
        
        # 割合でソートして上位3件を返す
        subject_ratios.sort(key=lambda x: x['ratio'], reverse=True)
        return [{'subject': item['subject'], 'level': item['level']} for item in subject_ratios[:3]]
    
    def _recommend_mixed(self, words_progress: List[Dict], sentences_progress: List[Dict], base_level: int, started_subjects: List[Tuple[str, int]], total_learnable: int) -> List[Dict]:
        """learnableが21-100の場合のレコメンド"""
        recommendations = []
        
        # 第一オススメ：learnableの割合が最も多い科目・レベル
        first_recommendation = self._get_highest_ratio_subject(words_progress, sentences_progress, base_level, total_learnable)
        if first_recommendation:
            recommendations.append(first_recommendation)
        
        # 第二オススメ：着手済みの中で未習語があるもの（最もレベルが低い）
        second_recommendation = self._get_lowest_started_with_unlearned(words_progress, sentences_progress, base_level, started_subjects)
        if second_recommendation and second_recommendation not in recommendations:
            recommendations.append(second_recommendation)
        
        # 第三オススメ：learnableの割合が二番目に多い科目・レベル
        if len(recommendations) < 3:
            third_recommendation = self._get_second_highest_ratio_subject(words_progress, sentences_progress, base_level, recommendations, total_learnable)
            if third_recommendation:
                recommendations.append(third_recommendation)
        
        return recommendations[:3]
    
    def _recommend_low_learnable(self, words_progress: List[Dict], sentences_progress: List[Dict], base_level: int, started_subjects: List[Tuple[str, int]], total_learnable: int) -> List[Dict]:
        """learnableが0-20の場合のレコメンド"""
        recommendations = []
        
        # 第一オススメ：着手済みの中で未習語があるもの（最もレベルが低い）
        first_recommendation = self._get_lowest_started_with_unlearned(words_progress, sentences_progress, base_level, started_subjects)
        if first_recommendation:
            recommendations.append(first_recommendation)
        else:
            # 未習語がなければ、まだ着手していない次のレベル
            next_level = self._get_next_unstarted_level(base_level, started_subjects)
            if next_level:
                recommendations.append(next_level)
        
        # 第二オススメ：learnableの割合が最も多い科目・レベル
        if len(recommendations) < 3:
            second_recommendation = self._get_highest_ratio_subject(words_progress, sentences_progress, base_level, total_learnable)
            if second_recommendation and second_recommendation not in recommendations:
                recommendations.append(second_recommendation)
        
        return recommendations[:3]
    
    def _get_highest_ratio_subject(self, words_progress: List[Dict], sentences_progress: List[Dict], base_level: int, total_learnable: int) -> Optional[Dict]:
        """learnableの割合が最も高い科目・レベルを取得"""
        max_ratio = 0
        best_subject = None
        
        for level in range(base_level, MAX_LEVEL + 1):
            # 単語の割合を計算
            words_data = next((p for p in words_progress if p.get('level') == level), None)
            if words_data and words_data.get('reviewable', 0) > 0:
                ratio = words_data['reviewable'] / total_learnable if total_learnable > 0 else 0
                if ratio > max_ratio:
                    max_ratio = ratio
                    best_subject = {'subject': 'words', 'level': level}
            
            # 例文の割合を計算
            sentences_data = next((p for p in sentences_progress if p.get('level') == level), None)
            if sentences_data and sentences_data.get('reviewable', 0) > 0:
                ratio = sentences_data['reviewable'] / total_learnable if total_learnable > 0 else 0
                if ratio > max_ratio:
                    max_ratio = ratio
                    best_subject = {'subject': 'sentences', 'level': level}
        
        return best_subject
    
    def _get_second_highest_ratio_subject(self, words_progress: List[Dict], sentences_progress: List[Dict], base_level: int, existing_recommendations: List[Dict], total_learnable: int) -> Optional[Dict]:
        """learnableの割合が二番目に高い科目・レベルを取得"""
        ratios = []
        
        for level in range(base_level, MAX_LEVEL + 1):
            # 単語の割合を計算
            words_data = next((p for p in words_progress if p.get('level') == level), None)
            if words_data and words_data.get('reviewable', 0) > 0:
                ratio = words_data['reviewable'] / total_learnable if total_learnable > 0 else 0
                subject_level = {'subject': 'words', 'level': level}
                if subject_level not in existing_recommendations:
                    ratios.append((ratio, subject_level))
            
            # 例文の割合を計算
            sentences_data = next((p for p in sentences_progress if p.get('level') == level), None)
            if sentences_data and sentences_data.get('reviewable', 0) > 0:
                ratio = sentences_data['reviewable'] / total_learnable if total_learnable > 0 else 0
                subject_level = {'subject': 'sentences', 'level': level}
                if subject_level not in existing_recommendations:
                    ratios.append((ratio, subject_level))
        
        # 割合でソートして二番目を返す
        ratios.sort(key=lambda x: x[0], reverse=True)
        return ratios[1][1] if len(ratios) > 1 else None
    
    def _get_lowest_started_with_unlearned(self, words_progress: List[Dict], sentences_progress: List[Dict], base_level: int, started_subjects: List[Tuple[str, int]]) -> Optional[Dict]:
        """着手済みの中で未習語がある最もレベルが低い科目・レベルを取得"""
        candidates = []
        
        for subject, level in started_subjects:
            if subject == 'words':
                progress_data = next((p for p in words_progress if p.get('level') == level), None)
            else:
                progress_data = next((p for p in sentences_progress if p.get('level') == level), None)
            
            if progress_data and progress_data.get('unlearned', 0) > 0:
                candidates.append({'subject': subject, 'level': level})
        
        if not candidates:
            return None
        
        # レベルでソート（同じレベルなら単語を優先）
        candidates.sort(key=lambda x: (x['level'], 0 if x['subject'] == 'words' else 1))
        return candidates[0]
    
    def _get_next_unstarted_level(self, base_level: int, started_subjects: List[Tuple[str, int]]) -> Optional[Dict]:
        """まだ着手していない次のレベルを取得"""
        # レベルと科目の組み合わせを生成（単語が例文より優先）
        level_subject_combinations = []
        for level in range(base_level, MAX_LEVEL + 1):
            level_subject_combinations.append(('words', level))
            level_subject_combinations.append(('sentences', level))
        
        # 着手済みでない最初の組み合わせを返す
        for subject, level in level_subject_combinations:
            if (subject, level) not in started_subjects:
                return {'subject': subject, 'level': level}
        
        return None
