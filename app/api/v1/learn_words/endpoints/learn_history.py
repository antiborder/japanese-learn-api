from fastapi import APIRouter, HTTPException, Depends
from common.schemas.learn_history import LearnHistoryRequest, LearnHistoryResponse, NextWordRequest, NextWordResponse, NoWordAvailableResponse
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

        # 3. 単語詳細をまとめて取得（batch_get_itemを使用）
        word_ids = [answer_word_id] + other_word_ids
        words_detail_dict = await next_service.batch_get_word_details(word_ids)
        
        # 辞書からリストに変換（元の順序を保持）し、存在しない単語をフィルタリング
        valid_words = []
        missing_word_ids = []
        for word_id in word_ids:
            result = words_detail_dict.get(word_id)
            if result is None:
                logger.warning(f"Word {word_id} not found in DynamoDB, skipping")
                missing_word_ids.append(word_id)
            else:
                valid_words.append(result)
        
        # 正解の単語が存在しない場合、エラーを返す
        if not valid_words or valid_words[0] is None:
            logger.error(f"Answer word {answer_word_id} not found in DynamoDB")
            raise HTTPException(status_code=404, detail=f"Answer word {answer_word_id} not found")
        
        answer_word = valid_words[0]
        
        # 他の単語が3つ未満の場合、追加で取得
        other_words = valid_words[1:]
        if len(other_words) < 3 and missing_word_ids:
            logger.info(f"Only {len(other_words)} valid words found, fetching additional words excluding {missing_word_ids}")
            additional_exclude_ids = [answer_word_id] + [w['id'] for w in other_words] + missing_word_ids
            additional_word_ids = await next_service.get_other_words(request.level, answer_word_id, additional_exclude_ids)
            
            if additional_word_ids:
                additional_details_dict = await next_service.batch_get_word_details(additional_word_ids)
                for word_id in additional_word_ids:
                    result = additional_details_dict.get(word_id)
                    if result is not None:
                        other_words.append(result)
                        if len(other_words) >= 3:
                            break
        
        # 他の単語が3つ未満の場合、エラーを返す
        if len(other_words) < 3:
            raise HTTPException(status_code=404, detail=f"Not enough valid words found. Only {len(other_words)} valid words available.")

        return {
            "mode": mode,
            "answer_word": answer_word,
            "other_words": other_words[:3]  # 最大3つまで
        }
    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
    except Exception as e:
        error_detail = str(e) if str(e) else repr(e)
        if hasattr(e, 'detail'):
            error_detail = e.detail
        logger.error(f"Error in get_next_word endpoint: {error_detail}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_detail if error_detail else "Internal server error")

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

        # 3. 単語詳細をまとめて取得（batch_get_itemを使用）
        word_ids = [answer_word_id] + other_word_ids
        words_detail_dict = await next_service.batch_get_word_details(word_ids)
        
        # 辞書からリストに変換（元の順序を保持）し、存在しない単語をフィルタリング
        valid_words = []
        missing_word_ids = []
        for word_id in word_ids:
            result = words_detail_dict.get(word_id)
            if result is None:
                logger.warning(f"Word {word_id} not found in DynamoDB, skipping")
                missing_word_ids.append(word_id)
            else:
                valid_words.append(result)
        
        # 正解の単語が存在しない場合、エラーを返す
        if not valid_words or valid_words[0] is None:
            logger.error(f"Answer word {answer_word_id} not found in DynamoDB")
            raise HTTPException(status_code=404, detail=f"Answer word {answer_word_id} not found")
        
        answer_word = valid_words[0]
        
        # 他の単語が3つ未満の場合、追加で取得
        other_words = valid_words[1:]
        if len(other_words) < 3 and missing_word_ids:
            logger.info(f"Only {len(other_words)} valid words found, fetching additional words excluding {missing_word_ids}")
            additional_exclude_ids = [answer_word_id] + [w['id'] for w in other_words] + missing_word_ids
            additional_word_ids = await next_service.get_other_words(request.level, answer_word_id, additional_exclude_ids)
            
            if additional_word_ids:
                additional_details_dict = await next_service.batch_get_word_details(additional_word_ids)
                for word_id in additional_word_ids:
                    result = additional_details_dict.get(word_id)
                    if result is not None:
                        other_words.append(result)
                        if len(other_words) >= 3:
                            break
        
        # 他の単語が3つ未満の場合、エラーを返す
        if len(other_words) < 3:
            raise HTTPException(status_code=404, detail=f"Not enough valid words found. Only {len(other_words)} valid words available.")

        return {
            "mode": mode,
            "answer_word": answer_word,
            "other_words": other_words[:3]  # 最大3つまで
        }
    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
    except Exception as e:
        error_detail = str(e) if str(e) else repr(e)
        if hasattr(e, 'detail'):
            error_detail = e.detail
        logger.error(f"Error in get_random_word endpoint: {error_detail}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_detail if error_detail else "Internal server error")