import logging
from typing import List, Dict
from integrations.dynamodb import progress_db, sentences_progress_db, kana_progress_db, user_settings_db
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
        1. kana(level = -10) reviewable >= 5
        2. kana(level = -10) unlearned >= 5
        3. kana(level = -9) reviewable >= 5
        4. kana(level = -9) unlearned >= 5
        5. kana(level = -7) reviewable >= 5
        6. kana(level = -7) unlearned >= 5
        7. kana(level = -6) reviewable >= 5
        8. kana(level = -6) unlearned >= 5
        5. words level N reviewable >= 10
        6. sentences level N reviewable >= 3
        7. words level N unlearned >= 10
        8. sentences level N unlearned >= 3

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

            # kanaの進捗を取得（一度だけ）
            kana_progress_list = await kana_progress_db.get_progress(user_id)
            kana_progress_by_level = {item["level"]: item for item in kana_progress_list}
            kana_neg10 = kana_progress_by_level.get(-10)
            kana_neg9 = kana_progress_by_level.get(-9)
            kana_neg7 = kana_progress_by_level.get(-7)
            kana_neg6 = kana_progress_by_level.get(-6)

            def _add_kana_rec(level: int) -> bool:
                rec = {"subject": "kana", "level": level}
                if rec not in recommendations:
                    recommendations.append(rec)
                return len(recommendations) >= 2

            # base_levelが0以下の場合のみ、kanaをチェック（base_levelが1以上の場合、kanaは推奨しない）
            if base_level <= 0:
                for kana, level in [(kana_neg10, -10), (kana_neg9, -9), (kana_neg7, -7), (kana_neg6, -6)]:
                    if kana and kana.get("reviewable", 0) >= 5:
                        if _add_kana_rec(level):
                            return recommendations
                    if kana and kana.get("unlearned", 0) >= 5:
                        if _add_kana_rec(level):
                            return recommendations

            # base_levelから順にレベル15まで見ていく
            for level in range(max(base_level, 1), min(MAX_LEVEL, 15) + 1):
                # レベルごとにwordsとsentencesのprogressを取得
                words_progress = await progress_db.get_progress_by_level(user_id, level)
                sentences_progress = await sentences_progress_db.get_progress_by_level(user_id, level)

                # 5. words level N reviewable >= 10
                if words_progress and words_progress.get("reviewable", 0) >= 10:
                    rec = {"subject": "words", "level": level}
                    if rec not in recommendations:
                        recommendations.append(rec)
                        if len(recommendations) >= 2:
                            return recommendations

                # 7. words level N unlearned >= 10
                if words_progress and words_progress.get("unlearned", 0) >= 10:
                    rec = {"subject": "words", "level": level}
                    if rec not in recommendations:
                        recommendations.append(rec)
                        if len(recommendations) >= 2:
                            return recommendations

                # 6. sentences level N reviewable >= 3
                if sentences_progress and sentences_progress.get("reviewable", 0) >= 3:
                    rec = {"subject": "sentences", "level": level}
                    if rec not in recommendations:
                        recommendations.append(rec)
                        if len(recommendations) >= 2:
                            return recommendations

                # 8. sentences level N unlearned >= 3
                if sentences_progress and sentences_progress.get("unlearned", 0) >= 3:
                    rec = {"subject": "sentences", "level": level}
                    if rec not in recommendations:
                        recommendations.append(rec)
                        if len(recommendations) >= 2:
                            return recommendations

            # ここまででおすすめが0個または1個の場合はそのまま返す
            return recommendations

        except Exception as e:
            logger.error(f"Error getting recommendations for user {user_id}: {str(e)}")
            return []
