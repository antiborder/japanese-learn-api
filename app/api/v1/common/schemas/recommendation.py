from pydantic import BaseModel, Field
from typing import List, Literal

class RecommendationItem(BaseModel):
    """レコメンド項目のスキーマ"""
    subject: Literal["words", "sentences", "kana"] = Field(..., description="科目（words、sentences、またはkana）")
    level: int = Field(..., ge=-10, le=15, description="レベル（-10-15）")

class RecommendationResponse(BaseModel):
    """レコメンドレスポンスのスキーマ"""
    recommendations: List[RecommendationItem] = Field(..., description="おすすめリスト（最大3件）")

