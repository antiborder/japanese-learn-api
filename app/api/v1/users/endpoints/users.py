from fastapi import APIRouter, HTTPException, Depends
from integrations.dynamodb import progress_db, plan_db, sentences_progress_db, sentences_plan_db
import logging
from common.auth import get_current_user_id

router = APIRouter()
logger = logging.getLogger(__name__)

# テスト用のユーザーID（本番環境では削除してください）
TEST_USER_ID = "test-user-123"

@router.get("/words/progress")
async def get_words_progress(current_user_id: str = Depends(get_current_user_id)):
    """
    ログインユーザーの単語のレベルごとの進捗情報を返す（unlearnedも含む）
    認証：必須（Bearerトークン）
    データ範囲：トークンから取得したユーザーIDのデータのみ
    """
    try:
        result = await progress_db.get_progress(current_user_id)
        return result
    except Exception as e:
        logger.error(f"Error in get_words_progress endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/words/plan")
async def get_words_plan(current_user_id: str = Depends(get_current_user_id)):
    """
    ログインユーザーの単語の今後のレビュー予定数を時間単位（24時間区切り）で集計して返す
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
        logger.error(f"Error in get_words_plan endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# テスト用エンドポイント（認証バイパス）
@router.get("/test/words/progress")
async def get_words_progress_test():
    """
    テスト用：認証なしでwords/progressエンドポイントをテスト
    本番環境では削除してください
    """
    try:
        result = await progress_db.get_progress(TEST_USER_ID)
        return result
    except Exception as e:
        logger.error(f"Error in get_words_progress_test endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/words/plan")
async def get_words_plan_test():
    """
    テスト用：認証なしでwords/planエンドポイントをテスト
    本番環境では削除してください
    """
    try:
        result = await plan_db.get_plan(TEST_USER_ID)
        return result
    except Exception as e:
        logger.error(f"Error in get_words_plan_test endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sentences/progress")
async def get_sentences_progress(current_user_id: str = Depends(get_current_user_id)):
    """
    ログインユーザーの例文のレベルごとの進捗情報を返す（unlearnedも含む）
    認証：必須（Bearerトークン）
    データ範囲：トークンから取得したユーザーIDのデータのみ
    """
    try:
        result = await sentences_progress_db.get_progress(current_user_id)
        return result
    except Exception as e:
        logger.error(f"Error in get_sentences_progress endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sentences/plan")
async def get_sentences_plan(current_user_id: str = Depends(get_current_user_id)):
    """
    ログインユーザーの例文の今後のレビュー予定数を時間単位（24時間区切り）で集計して返す
    認証：必須（Bearerトークン）
    データ範囲：トークンから取得したユーザーIDのデータのみ
    
    レスポンス形式：
    [
      { "time_slot": 0, "count": 12 },   # 現在時刻以前（過去の例文）
      { "time_slot": 1, "count": 18 },   # 現在から24時間以内
      { "time_slot": 2, "count": 25 },   # 24時間から48時間以内
      ...
    ]
    
    time_slot: 時間スロット番号（0=過去、1=0-24時間、2=24-48時間...）
    count: その時間スロット内の例文数
    """
    try:
        result = await sentences_plan_db.get_plan(current_user_id)
        return result
    except Exception as e:
        logger.error(f"Error in get_sentences_plan endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# テスト用エンドポイント（認証バイパス）
@router.get("/test/sentences/progress")
async def get_sentences_progress_test():
    """
    テスト用：認証なしでsentences/progressエンドポイントをテスト
    本番環境では削除してください
    """
    try:
        result = await sentences_progress_db.get_progress(TEST_USER_ID)
        return result
    except Exception as e:
        logger.error(f"Error in get_sentences_progress_test endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/sentences/plan")
async def get_sentences_plan_test():
    """
    テスト用：認証なしでsentences/planエンドポイントをテスト
    本番環境では削除してください
    """
    try:
        result = await sentences_plan_db.get_plan(TEST_USER_ID)
        return result
    except Exception as e:
        logger.error(f"Error in get_sentences_plan_test endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
