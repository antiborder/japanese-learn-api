from fastapi import APIRouter, HTTPException, Depends
from common.schemas.learn_history import LearnHistoryRequest, LearnHistoryResponse, NextWordRequest, NextWordResponse, NoWordAvailableResponse
from integrations.dynamodb_integration import learn_history_db
from utils.auth import get_current_user_id
import logging
from pydantic import BaseModel, Field
from typing import List, Union
from datetime import datetime, timezone

router = APIRouter()
logger = logging.getLogger(__name__)

def parse_datetime_with_tz(dt_str):
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        # タイムゾーン情報がなければUTCとして扱う
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

@router.post("/", response_model=LearnHistoryResponse)
async def record_learning(request: LearnHistoryRequest, current_user_id: str = Depends(get_current_user_id)):
    """
    学習履歴を記録し、次の学習情報を返します。
    認証：必須（Bearerトークン）
    データ範囲：トークンから取得したユーザーIDのデータのみ
    """
    try:
        result = await learn_history_db.record_learning(
            user_id=current_user_id,
            word_id=request.word_id,
            level=request.level,
            confidence=request.confidence,
            time=request.time
        )
        return result
    except Exception as e:
        logger.error(f"Error in record_learning endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/next", response_model=Union[dict, NoWordAvailableResponse])
async def get_next_word(request: NextWordRequest, current_user_id: str = Depends(get_current_user_id)):
    """
    次に学習すべき単語を取得します。
    認証：必須（Bearerトークン）
    データ範囲：トークンから取得したユーザーIDのデータのみ
    
    levelパラメータ：
    - 数値（1-14）：指定されたレベルから単語を取得
    - "REVIEW_ALL"：全レベルから復習可能な単語（next_datetimeが最も古いもの）を取得
    """
    try:
        # 1. 出題単語IDとモード取得
        next_result = await learn_history_db.get_next_word(
            user_id=current_user_id,
            level=request.level
        )
        if not next_result:
            raise HTTPException(status_code=404, detail="No words found for the specified level")
        
        # 単語がない場合のレスポンスをチェック
        if next_result.get('no_word_available'):
            return NoWordAvailableResponse(
                next_available_datetime=next_result.get('next_available_datetime')
            )
        
        answer_word_id = int(next_result['answer_word_id'])
        mode = next_result['mode']

        # 2. 他の単語ID取得
        other_word_ids = await learn_history_db.get_other_words(request.level, answer_word_id)
        if not other_word_ids or len(other_word_ids) < 3:
            raise HTTPException(status_code=404, detail="Not enough words found for the specified level")

        # 3. 単語詳細をまとめて取得
        word_ids = [answer_word_id] + other_word_ids
        words_detail = [await learn_history_db.get_word_detail(word_id) for word_id in word_ids]
        answer_word = words_detail[0]
        other_words = words_detail[1:]

        return {
            "mode": mode,
            "answer_word": answer_word,
            "other_words": other_words
        }
    except Exception as e:
        logger.error(f"Error in get_next_word endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class OtherWordsRequest(BaseModel):
    level: int = Field(..., description="取得する単語のレベル")
    answer_word_id: int = Field(..., description="正解の単語ID（このIDは選択肢から除外されます）")

@router.post("/other_words", response_model=List[int])
async def get_other_words(request: OtherWordsRequest) -> List[int]:
    """指定されたレベルで、正解の単語ID以外の単語を3つ取得します。
    
    このエンドポイントは、クイズの選択肢として使用する単語を取得します。
    指定されたレベルに属し、正解の単語IDと異なる単語からランダムに3つを選択します。
    
    Args:
        request: OtherWordsRequest
            - level: 取得する単語のレベル
            - answer_word_id: 正解の単語ID（このIDは選択肢から除外されます）
    
    Returns:
        List[int]: 3つの単語IDのリスト（選択肢として使用する単語）
    
    Raises:
        HTTPException: 404 - 条件に合致する単語が3つ未満の場合
        HTTPException: 500 - その他のエラー
    """
    try:
        word_ids = await learn_history_db.get_other_words(request.level, request.answer_word_id)
        if not word_ids:
            raise HTTPException(status_code=404, detail="Not enough words found for the specified level")
        return word_ids
    except Exception as e:
        logger.error(f"Error getting other words: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/progress")
async def get_progress(current_user_id: str = Depends(get_current_user_id)):
    """
    ログインユーザーのレベルごとの進捗情報を返す（unlearnedも含む）
    認証：必須（Bearerトークン）
    データ範囲：トークンから取得したユーザーIDのデータのみ
    """
    try:
        # ユーザーの学習履歴を全て取得
        user_response = learn_history_db.table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
            ExpressionAttributeValues={
                ':pk': f"USER#{current_user_id}",
                ':sk_prefix': 'WORD#'
            }
        )
        user_items = user_response.get('Items', [])
        now = datetime.now(timezone.utc)
        result = []
        for level in range(1, 15):
            # 各レベルの全単語IDリストをPKで直接query
            word_response = learn_history_db.table.query(
                KeyConditionExpression='PK = :pk AND SK = :sk',
                ExpressionAttributeValues={
                    ':pk': f'WORDS#{level}',
                    ':sk': 'METADATA'
                }
            )
            all_word_ids = set(int(item['word_id']) for item in word_response.get('Items', []))
            # ユーザーの学習済み単語IDリスト
            level_user_items = [item for item in user_items if item.get('level') == level]
            user_learned_ids = set(int(item['word_id']) for item in level_user_items)
            learned = len(user_learned_ids)
            unlearned = len(all_word_ids - user_learned_ids)
            reviewable = sum(
                1 for item in level_user_items
                if 'next_datetime' in item and parse_datetime_with_tz(item['next_datetime']) <= now
            )
            if level_user_items:
                avg_progress = sum(float(item.get('proficiency_MJ', 0)) + float(item.get('proficiency_JM', 0)) for item in level_user_items) / (2 * learned)
                progress = int(round(avg_progress * 100))
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
        logger.error(f"Error in get_progress endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plan")
async def get_plan(current_user_id: str = Depends(get_current_user_id)):
    """
    ログインユーザーの今後のレビュー予定数を時間単位（24時間区切り）で集計して返す
    認証：必須（Bearerトークン）
    データ範囲：トークンから取得したユーザーIDのデータのみ
    
    レスポンス形式：
    [
      { "time_slot": 0, "count": 12 },   # 現在時刻以前（過去の単語）
      { "time_slot": 1, "count": 18 },   # 現在から24時間以内
      { "time_slot": 2, "count": 25 },   # 24時間から48時間以内
      ...
    ]
    
    time_slot: 時間スロット番号（0=過去、1=0-24時間、2=24-48時間...）
    count: その時間スロット内の単語数
    """
    try:
        # ユーザーの学習履歴を全て取得
        user_response = learn_history_db.table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
            ExpressionAttributeValues={
                ':pk': f"USER#{current_user_id}",
                ':sk_prefix': 'WORD#'
            }
        )
        user_items = user_response.get('Items', [])
        now = datetime.now(timezone.utc)
        
        logger.info(f"Current time (UTC): {now}")
        logger.info(f"Total user items found: {len(user_items)}")
        
        # 時間スロットごとのカウントを初期化
        plan_counts = {}
        past_count = 0  # デバッグ用
        
        for item in user_items:
            next_dt_str = item.get('next_datetime')
            if not next_dt_str:
                logger.warning(f"Item {item.get('word_id')} has no next_datetime")
                continue
            try:
                next_dt = datetime.fromisoformat(next_dt_str)
                if next_dt.tzinfo is None:
                    next_dt = next_dt.replace(tzinfo=timezone.utc)
            except Exception as e:
                logger.warning(f"Invalid next_datetime format for word {item.get('word_id')}: {e}")
                continue
            
            # 現在時刻との差を時間単位で計算
            time_diff = next_dt - now
            hours_diff = time_diff.total_seconds() / 3600
            
            # 時間スロットを決定
            if hours_diff <= 0:
                # 過去の単語（現在時刻以前）
                time_slot = 0
                past_count += 1
                logger.info(f"Past word found: word_id={item.get('word_id')}, next_datetime={next_dt}, hours_diff={hours_diff}")
            else:
                # 未来の単語（24時間単位でスロット分け）
                time_slot = int(hours_diff // 24) + 1
            
            plan_counts[time_slot] = plan_counts.get(time_slot, 0) + 1
        
        logger.info(f"Total past words found: {past_count}")
        logger.info(f"Plan counts: {plan_counts}")
        
        # time_slot: 0を常に含める（過去の単語がない場合もcount: 0で含める）
        if 0 not in plan_counts:
            plan_counts[0] = 0
        
        # 時間スロット順で返す（過去から未来へ）
        result = [
            {"time_slot": time_slot, "count": count}
            for time_slot, count in sorted(plan_counts.items())
        ]
        return result
    except Exception as e:
        logger.error(f"Error in get_plan endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class RandomWordRequest(BaseModel):
    level: int = Field(..., description="取得する単語のレベル")

@router.post("/next/random")
async def get_random_word(request: RandomWordRequest):
    """
    指定されたレベルからランダムに単語を1つ取得します。
    認証は不要です。
    """
    try:
        # 1. ランダムに単語IDとモードを取得
        next_result = await learn_history_db.get_random_word(level=request.level)
        if not next_result:
            raise HTTPException(status_code=404, detail="No words found for the specified level")
        
        answer_word_id = int(next_result['answer_word_id'])
        mode = next_result['mode']

        # 2. 他の単語IDを取得
        other_word_ids = await learn_history_db.get_other_words(request.level, answer_word_id)
        if not other_word_ids or len(other_word_ids) < 3:
            raise HTTPException(status_code=404, detail="Not enough words found for the specified level")

        # 3. 単語詳細をまとめて取得
        word_ids = [answer_word_id] + other_word_ids
        words_detail = [await learn_history_db.get_word_detail(word_id) for word_id in word_ids]
        answer_word = words_detail[0]
        other_words = words_detail[1:]

        return {
            "mode": mode,
            "answer_word": answer_word,
            "other_words": other_words
        }
    except Exception as e:
        logger.error(f"Error in get_random_word endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))