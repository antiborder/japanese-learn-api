from fastapi import APIRouter, HTTPException, Depends
from schemas.recommendation import RecommendationResponse, RecommendationItem
from services.recommendation_service import RecommendationService
from common.auth import get_current_user_id
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(current_user_id: str = Depends(get_current_user_id)):
    """
    ユーザーの学習レコメンドを取得する
    
    次はどの科目のどのレベルを学習すべきかお勧めを表示する機能です。
    ユーザーページと、各学習の終了後に表示されます。
    
    Returns:
        RecommendationResponse: おすすめリスト（最大3件）
    """
    try:
        recommendation_service = RecommendationService()
        recommendations = await recommendation_service.get_recommendations(current_user_id)
        
        # レスポンス形式に変換
        recommendation_items = [
            RecommendationItem(subject=rec['subject'], level=rec['level'])
            for rec in recommendations
        ]
        
        return RecommendationResponse(recommendations=recommendation_items)
        
    except Exception as e:
        logger.error(f"Error getting recommendations for user {current_user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")
