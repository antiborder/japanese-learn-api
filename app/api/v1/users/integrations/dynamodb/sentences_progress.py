import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from .base import DynamoDBBase
from services.datetime_utils import DateTimeUtils
from common.config import MIN_LEVEL, MAX_LEVEL, GROUP_TO_LEVELS

logger = logging.getLogger(__name__)

class SentencesProgressDynamoDB(DynamoDBBase):
    def __init__(self):
        super().__init__()
        self.datetime_utils = DateTimeUtils()

    def _get_level_sentences(self, level: int) -> List[Dict]:
        """指定されたレベルの例文を取得します（word-level-index GSIを使用）"""
        try:
            response = self.table.query(
                IndexName='word-level-index',
                KeyConditionExpression="PK = :pk AND #level = :level",
                ExpressionAttributeNames={
                    "#level": "level"
                },
                ExpressionAttributeValues={
                    ":pk": "SENTENCE",
                    ":level": int(level)
                }
            )
            level_sentences = response.get('Items', [])
            if not level_sentences:
                logger.debug(f"No sentences found for level {level}")
                return []
            
            logger.debug(f"Successfully retrieved {len(level_sentences)} sentences for level {level}")
            return level_sentences
        except Exception as e:
            logger.error(f"Error getting sentences for level {level}: {str(e)}")
            # インデックスが存在しない場合のフォールバック（既存の全件取得）
            logger.warning(f"Falling back to full sentence list for level {level}")
            return []
    
    def _get_all_sentences_with_pagination(self) -> List[Dict]:
        """全例文をページネーション対応で取得（フォールバック用）"""
        all_sentences = []
        last_evaluated_key = None
        
        while True:
            if last_evaluated_key:
                response = self.table.query(
                    KeyConditionExpression='PK = :pk',
                    ExpressionAttributeValues={
                        ':pk': 'SENTENCE'
                    },
                    ExclusiveStartKey=last_evaluated_key
                )
            else:
                response = self.table.query(
                    KeyConditionExpression='PK = :pk',
                    ExpressionAttributeValues={
                        ':pk': 'SENTENCE'
                    }
                )
            
            all_sentences.extend(response.get('Items', []))
            
            last_evaluated_key = response.get('LastEvaluatedKey')
            if not last_evaluated_key:
                break
        
        return all_sentences

    async def get_progress(self, current_user_id: str, group: Optional[str] = None) -> List[Dict]:
        """
        ログインユーザーの例文のレベルごとの進捗情報を返す（unlearnedも含む）
        
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
            
            # ユーザーの例文学習履歴を全て取得
            user_response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f"USER#{current_user_id}",
                    ':sk_prefix': 'SENTENCE#'
                }
            )
            user_items = user_response.get('Items', [])
            
            # 必要なレベルの例文のみを取得（word-level-index GSIを使用）
            sentences_by_level = {}
            for level in target_levels:
                level_sentences = self._get_level_sentences(level)
                if level_sentences:
                    sentences_by_level[level] = level_sentences
            
            # インデックス取得が失敗した場合のフォールバック
            if not sentences_by_level and target_levels:
                logger.warning("Level-based query failed, falling back to full sentence list")
                all_sentences = self._get_all_sentences_with_pagination()
                for sentence in all_sentences:
                    sentence_level = sentence.get('level')
                    if sentence_level and sentence_level in target_levels:
                        if sentence_level not in sentences_by_level:
                            sentences_by_level[sentence_level] = []
                        sentences_by_level[sentence_level].append(sentence)
            
            now = datetime.now(timezone.utc)
            result = []
            for level in target_levels:
                # レベルごとの全例文IDを取得
                level_sentences = sentences_by_level.get(level, [])
                all_sentence_ids = set(int(item['SK']) for item in level_sentences)
                
                # ユーザーの学習済み例文IDリスト
                level_user_items = [item for item in user_items if item.get('level') == level]
                user_learned_ids = set(int(item['sentence_id']) for item in level_user_items)
                learned = len(user_learned_ids)
                unlearned = len(all_sentence_ids - user_learned_ids)
                reviewable = sum(
                    1 for item in level_user_items
                    if self.datetime_utils.is_reviewable(item)
                )
                if level_user_items:
                    # 学習済み例文の習熟度の平均を計算
                    gross_proficiency = sum(float(item.get('proficiency', 0)) for item in level_user_items)
                    avg_proficiency_of_learned = gross_proficiency / learned if learned > 0 else 0
                    
                    # 全体の進捗率を計算（学習済み例文数 / 全例文数）
                    learned_ratio = learned / len(all_sentence_ids) if len(all_sentence_ids) > 0 else 0
                    
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
            logger.error(f"Error in get_sentences_progress: {str(e)}")
            raise
