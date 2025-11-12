from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from integrations.dynamodb import (
    progress_db,
    plan_db,
    sentences_progress_db,
    sentences_plan_db,
    kana_progress_db,
    kana_plan_db,
    user_settings_db,
)
from common.schemas.user_settings import UserSettingsCreate, UserSettingsUpdate, UserSettingsResponse
from common.config import VALID_GROUPS
import logging
from common.auth import get_current_user_id

router = APIRouter()
logger = logging.getLogger(__name__)

# テスト用のユーザーID（本番環境では削除してください）
TEST_USER_ID = "test-user-123"

@router.get("/words/progress")
async def get_words_progress(
    current_user_id: str = Depends(get_current_user_id),
    group: str = Query(..., description="級を指定する文字列（N5, N4, N3, N2, N1）")
):
    """
    ログインユーザーの単語のレベルごとの進捗情報を返す（unlearnedも含む）
    認証：必須（Bearerトークン）
    データ範囲：トークンから取得したユーザーIDのデータのみ
    
    パラメータ:
    - group: 必須。級パラメータ。指定された級に属するレベルのprogressを返す。
            有効な値: N5, N4, N3, N2, N1
            - N5: レベル 1, 2, 3
            - N4: レベル 4, 5, 6
            - N3: レベル 7, 8, 9
            - N2: レベル 10, 11, 12
            - N1: レベル 13, 14, 15
    """
    try:
        # groupパラメータのバリデーション
        if group not in VALID_GROUPS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid group: {group}. Valid groups are: {VALID_GROUPS}"
            )
        
        result = await progress_db.get_progress(current_user_id, group=group)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in get_words_progress endpoint: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_words_progress endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/words/plan")
async def get_words_plan(current_user_id: str = Depends(get_current_user_id)):
    """
    ログインユーザーの単語の今後のレビュー予定数を時間単位（24時間区切り）で集計して返す
    認証：必須（Bearerトークン）
    データ範囲：トークンから取得したユーザーIDのデータのみ
    base_level以上のレベルの単語のみが含まれる
    
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
        # ユーザー設定を取得してbase_levelを取得
        user_settings = await user_settings_db.get_user_settings(current_user_id)
        base_level = user_settings.base_level if user_settings else None
        
        result = await plan_db.get_plan(current_user_id, base_level=base_level)
        return result
    except Exception as e:
        logger.error(f"Error in get_words_plan endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# テスト用エンドポイント（認証バイパス）
@router.get("/test/words/progress")
async def get_words_progress_test(
    group: str = Query(..., description="級を指定する文字列（N5, N4, N3, N2, N1）")
):
    """
    テスト用：認証なしでwords/progressエンドポイントをテスト
    本番環境では削除してください
    """
    try:
        # groupパラメータのバリデーション
        if group not in VALID_GROUPS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid group: {group}. Valid groups are: {VALID_GROUPS}"
            )
        
        result = await progress_db.get_progress(TEST_USER_ID, group=group)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in get_words_progress_test endpoint: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
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
async def get_sentences_progress(
    current_user_id: str = Depends(get_current_user_id),
    group: str = Query(..., description="級を指定する文字列（N5, N4, N3, N2, N1）")
):
    """
    ログインユーザーの例文のレベルごとの進捗情報を返す（unlearnedも含む）
    認証：必須（Bearerトークン）
    データ範囲：トークンから取得したユーザーIDのデータのみ
    
    パラメータ:
    - group: 必須。級パラメータ。指定された級に属するレベルのprogressを返す。
            有効な値: N5, N4, N3, N2, N1
            - N5: レベル 1, 2, 3
            - N4: レベル 4, 5, 6
            - N3: レベル 7, 8, 9
            - N2: レベル 10, 11, 12
            - N1: レベル 13, 14, 15
    """
    try:
        # groupパラメータのバリデーション
        if group not in VALID_GROUPS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid group: {group}. Valid groups are: {VALID_GROUPS}"
            )
        
        result = await sentences_progress_db.get_progress(current_user_id, group=group)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in get_sentences_progress endpoint: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_sentences_progress endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sentences/plan")
async def get_sentences_plan(current_user_id: str = Depends(get_current_user_id)):
    """
    ログインユーザーの例文の今後のレビュー予定数を時間単位（24時間区切り）で集計して返す
    認証：必須（Bearerトークン）
    データ範囲：トークンから取得したユーザーIDのデータのみ
    base_level以上のレベルの例文のみが含まれる
    
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
        # ユーザー設定を取得してbase_levelを取得
        user_settings = await user_settings_db.get_user_settings(current_user_id)
        base_level = user_settings.base_level if user_settings else None
        
        result = await sentences_plan_db.get_plan(current_user_id, base_level=base_level)
        return result
    except Exception as e:
        logger.error(f"Error in get_sentences_plan endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# テスト用エンドポイント（認証バイパス）
@router.get("/test/sentences/progress")
async def get_sentences_progress_test(
    group: str = Query(..., description="級を指定する文字列（N5, N4, N3, N2, N1）")
):
    """
    テスト用：認証なしでsentences/progressエンドポイントをテスト
    本番環境では削除してください
    """
    try:
        # groupパラメータのバリデーション
        if group not in VALID_GROUPS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid group: {group}. Valid groups are: {VALID_GROUPS}"
            )
        
        result = await sentences_progress_db.get_progress(TEST_USER_ID, group=group)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in get_sentences_progress_test endpoint: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
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


@router.get("/kana/progress")
async def get_kana_progress(current_user_id: str = Depends(get_current_user_id)):
    """
    ログインユーザーのかなのレベルごとの進捗情報を返す。
    レベルは -10 から 0 までを固定順で返却します。
    """
    try:
        result = await kana_progress_db.get_progress(current_user_id)
        return result
    except Exception as e:
        logger.error(f"Error in get_kana_progress endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/kana/progress")
async def get_kana_progress_test():
    """
    テスト用：認証なしでkana/progressエンドポイントをテスト
    本番環境では削除してください
    """
    try:
        result = await kana_progress_db.get_progress(TEST_USER_ID)
        return result
    except Exception as e:
        logger.error(f"Error in get_kana_progress_test endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kana/plan")
async def get_kana_plan(current_user_id: str = Depends(get_current_user_id)):
    """
    ログインユーザーのかなの今後のレビュー予定数を時間単位（24時間区切り）で集計して返す
    認証：必須（Bearerトークン）
    データ範囲：トークンから取得したユーザーIDのデータのみ
    base_levelが-10または0より大きい場合は空のレスポンスを返す
    """
    try:
        # ユーザー設定を取得してbase_levelを確認
        user_settings = await user_settings_db.get_user_settings(current_user_id)
        if user_settings and (user_settings.base_level == -10 or user_settings.base_level > 0):
            return []
        
        result = await kana_plan_db.get_plan(current_user_id)
        return result
    except Exception as e:
        logger.error(f"Error in get_kana_plan endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/kana/plan")
async def get_kana_plan_test():
    """
    テスト用：認証なしでkana/planエンドポイントをテスト
    本番環境では削除してください
    """
    try:
        result = await kana_plan_db.get_plan(TEST_USER_ID)
        return result
    except Exception as e:
        logger.error(f"Error in get_kana_plan_test endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ユーザー設定関連のエンドポイント
@router.get("/settings")
async def get_user_settings(current_user_id: str = Depends(get_current_user_id)):
    """
    ログインユーザーの設定を取得する
    認証：必須（Bearerトークン）
    """
    try:
        settings = await user_settings_db.get_user_settings(current_user_id)
        if not settings:
            raise HTTPException(status_code=404, detail="User settings not found")
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_user_settings endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings")
async def create_user_settings(
    settings: UserSettingsCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    ログインユーザーの設定を作成する
    認証：必須（Bearerトークン）
    """
    try:
        # 既存の設定があるかチェック
        existing_settings = await user_settings_db.get_user_settings(current_user_id)
        if existing_settings:
            raise HTTPException(status_code=409, detail="User settings already exist. Use PUT to update.")
        
        result = await user_settings_db.create_user_settings(current_user_id, settings)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_user_settings endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/settings")
async def update_user_settings(
    settings: UserSettingsUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    ログインユーザーの設定を更新する
    認証：必須（Bearerトークン）
    """
    try:
        result = await user_settings_db.update_user_settings(current_user_id, settings)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in update_user_settings endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/settings")
async def delete_user_settings(current_user_id: str = Depends(get_current_user_id)):
    """
    ログインユーザーの設定を削除する
    認証：必須（Bearerトークン）
    """
    try:
        await user_settings_db.delete_user_settings(current_user_id)
        return {"message": "User settings deleted successfully"}
    except Exception as e:
        logger.error(f"Error in delete_user_settings endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# テスト用エンドポイント（認証バイパス）
@router.get("/test/settings")
async def get_user_settings_test():
    """
    テスト用：認証なしでsettingsエンドポイントをテスト
    本番環境では削除してください
    """
    try:
        settings = await user_settings_db.get_user_settings(TEST_USER_ID)
        if not settings:
            raise HTTPException(status_code=404, detail="User settings not found")
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_user_settings_test endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/settings")
async def create_user_settings_test(settings: UserSettingsCreate):
    """
    テスト用：認証なしでsettings作成エンドポイントをテスト
    本番環境では削除してください
    """
    try:
        result = await user_settings_db.create_user_settings(TEST_USER_ID, settings)
        return result
    except Exception as e:
        logger.error(f"Error in create_user_settings_test endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/test/settings")
async def update_user_settings_test(settings: UserSettingsUpdate):
    """
    テスト用：認証なしでsettings更新エンドポイントをテスト
    本番環境では削除してください
    """
    try:
        result = await user_settings_db.update_user_settings(TEST_USER_ID, settings)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in update_user_settings_test endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
