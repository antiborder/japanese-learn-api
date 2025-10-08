from fastapi import APIRouter, HTTPException, Depends
from common.schemas.learn_history import LearnHistoryRequest, LearnHistoryResponse, NextWordRequest, NextWordResponse, NoWordAvailableResponse
from integrations.dynamodb import progress_db, plan_db
from services.learning_service import LearningService
from services.next_service import NextService
import logging
from pydantic import BaseModel, Field
from typing import List, Union
from datetime import datetime, timezone
from common.auth import get_current_user_id

router = APIRouter()
logger = logging.getLogger(__name__)

# サービスのインスタンスを作成
learning_service = LearningService()
next_service = NextService()

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
        result = await learning_service.record_learning(
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
    - 数値（1-15）：指定されたレベルから単語を取得
    - "REVIEW_ALL"：全レベルから復習可能な単語（next_datetimeが最も古いもの）を取得
    """
    try:
        # 1. 出題単語IDとモード取得
        next_result = await next_service.get_next_word(
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
        other_word_ids = await next_service.get_other_words(request.level, answer_word_id)
        if not other_word_ids or len(other_word_ids) < 3:
            raise HTTPException(status_code=404, detail="Not enough words found for the specified level")

        # 3. 単語詳細をまとめて取得
        word_ids = [answer_word_id] + other_word_ids
        import asyncio
        words_detail = await asyncio.gather(*[next_service.get_word_detail(word_id) for word_id in word_ids])
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
        word_ids = await next_service.get_other_words(request.level, request.answer_word_id)
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
        result = await progress_db.get_progress(current_user_id)
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
        result = await plan_db.get_plan(current_user_id)
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
        next_result = await next_service.get_random_word(level=request.level)
        if not next_result:
            raise HTTPException(status_code=404, detail="No words found for the specified level")
        
        answer_word_id = int(next_result['answer_word_id'])
        mode = next_result['mode']

        # 2. 他の単語IDを取得
        other_word_ids = await next_service.get_other_words(request.level, answer_word_id)
        if not other_word_ids or len(other_word_ids) < 3:
            raise HTTPException(status_code=404, detail="Not enough words found for the specified level")

        # 3. 単語詳細をまとめて取得
        word_ids = [answer_word_id] + other_word_ids
        import asyncio
        words_detail = await asyncio.gather(*[next_service.get_word_detail(word_id) for word_id in word_ids])
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