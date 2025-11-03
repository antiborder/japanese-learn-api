import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from .base import DynamoDBBase
from services.datetime_utils import DateTimeUtils
from common.config import MIN_LEVEL, MAX_LEVEL, GROUP_TO_LEVELS

logger = logging.getLogger(__name__)

class ProgressDynamoDB(DynamoDBBase):
    def __init__(self):
        super().__init__()
        self.datetime_utils = DateTimeUtils()

    def _get_level_words(self, level: int) -> List[Dict]:
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
                logger.debug(f"No words found for level {level}")
                return []
            
            logger.debug(f"Successfully retrieved {len(level_words)} words for level {level}")
            return level_words
        except Exception as e:
            logger.error(f"Error getting words for level {level}: {str(e)}")
            # インデックスが存在しない場合のフォールバック（既存の全件取得）
            logger.warning(f"Falling back to full word list for level {level}")
            return []
    
    def _get_all_words_with_pagination(self) -> List[Dict]:
        """全単語をページネーション対応で取得（フォールバック用）"""
        all_words = []
        last_evaluated_key = None
        
        while True:
            if last_evaluated_key:
                response = self.table.query(
                    KeyConditionExpression='PK = :pk',
                    ExpressionAttributeValues={
                        ':pk': 'WORD'
                    },
                    ExclusiveStartKey=last_evaluated_key
                )
            else:
                response = self.table.query(
                    KeyConditionExpression='PK = :pk',
                    ExpressionAttributeValues={
                        ':pk': 'WORD'
                    }
                )
            
            all_words.extend(response.get('Items', []))
            
            last_evaluated_key = response.get('LastEvaluatedKey')
            if not last_evaluated_key:
                break
        
        return all_words

    async def get_progress(self, current_user_id: str, group: Optional[str] = None) -> List[Dict]:
        """
        ログインユーザーのレベルごとの進捗情報を返す（unlearnedも含む）
        
        Args:
            current_user_id: ユーザーID
            group: オプショナルな級パラメータ（N5, N4, N3, N2, N1）
                  指定された場合、その級に属するレベルのprogressのみを返す
        """
        try:
            # フィルタリングするレベルを決定
            if group:
                if group not in GROUP_TO_LEVELS:
                    raise ValueError(f"Invalid group: {group}. Valid groups are: {list(GROUP_TO_LEVELS.keys())}")
                target_levels = GROUP_TO_LEVELS[group]
            else:
                target_levels = list(range(MIN_LEVEL, MAX_LEVEL + 1))
            
            # ユーザーの学習履歴を全て取得
            user_response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f"USER#{current_user_id}",
                    ':sk_prefix': 'WORD#'
                }
            )
            user_items = user_response.get('Items', [])
            
            # 必要なレベルの単語のみを取得（word-level-index GSIを使用）
            words_by_level = {}
            for level in target_levels:
                level_words = self._get_level_words(level)
                if level_words:
                    words_by_level[level] = level_words
            
            # インデックス取得が失敗した場合のフォールバック
            if not words_by_level and target_levels:
                logger.warning("Level-based query failed, falling back to full word list")
                all_words = self._get_all_words_with_pagination()
                for word in all_words:
                    word_level = word.get('level')
                    if word_level and word_level in target_levels:
                        if word_level not in words_by_level:
                            words_by_level[word_level] = []
                        words_by_level[word_level].append(word)
            
            now = datetime.now(timezone.utc)
            result = []
            for level in target_levels:
                # レベルごとの全単語IDを取得
                level_words = words_by_level.get(level, [])
                all_word_ids = set(int(item['SK']) for item in level_words)
                
                # ユーザーの学習済み単語IDリスト
                level_user_items = [item for item in user_items if item.get('level') == level]
                user_learned_ids = set(int(item['word_id']) for item in level_user_items)
                learned = len(user_learned_ids)
                unlearned = len(all_word_ids - user_learned_ids)
                reviewable = sum(
                    1 for item in level_user_items
                    if self.datetime_utils.is_reviewable(item)
                )
                if level_user_items:
                    # 学習済み単語の習熟度の平均を計算
                    gross_proficiency = sum(float(item.get('proficiency_MJ', 0)) + float(item.get('proficiency_JM', 0)) for item in level_user_items)
                    avg_proficiency_of_learned = gross_proficiency / (2 * learned) if learned > 0 else 0
                    
                    # 全体の進捗率を計算（学習済み単語数 / 全単語数）
                    learned_ratio = learned / len(all_word_ids) if len(all_word_ids) > 0 else 0
                    
                    # 最終的なproficiencyは、完了率と習熟度の平均を組み合わせる
                    # 完了率が高いほど、習熟度の重みが高くなる
                    progress = int(round((learned_ratio * avg_proficiency_of_learned) * 100))
                else:
                    progress = 0
                result.append({
                    "level": level,
                    "progress": progress,
                    "reviewable": reviewable,
                    "learned": learned,
                    "unlearned": unlearned
                })
            return result
        except Exception as e:
            logger.error(f"Error in get_progress: {str(e)}")
            raise
