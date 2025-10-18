from fastapi import APIRouter, HTTPException, Depends
from integrations.dynamodb import progress_db, plan_db
import logging
from common.auth import get_current_user_id

router = APIRouter()
logger = logging.getLogger(__name__)

# テスト用のユーザーID（本番環境では削除してください）
TEST_USER_ID = "test-user-123"

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

# テスト用エンドポイント（認証バイパス）
@router.get("/test/progress")
async def get_progress_test():
    """
    テスト用：認証なしでprogressエンドポイントをテスト
    本番環境では削除してください
    """
    try:
        result = await progress_db.get_progress(TEST_USER_ID)
        return result
    except Exception as e:
        logger.error(f"Error in get_progress_test endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/plan")
async def get_plan_test():
    """
    テスト用：認証なしでplanエンドポイントをテスト
    本番環境では削除してください
    """
    try:
        result = await plan_db.get_plan(TEST_USER_ID)
        return result
    except Exception as e:
        logger.error(f"Error in get_plan_test endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
