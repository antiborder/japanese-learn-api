from pydantic import BaseModel, Field
from typing import List, Literal

class RecommendationItem(BaseModel):
    """レコメンド項目のスキーマ"""
    subject: Literal["words", "sentences"] = Field(..., description="科目（wordsまたはsentences）")
    level: int = Field(..., ge=1, le=15, description="レベル（1-15）")

class RecommendationResponse(BaseModel):
    """レコメンドレスポンスのスキーマ"""
    recommendations: List[RecommendationItem] = Field(..., description="おすすめリスト（最大3件）")

