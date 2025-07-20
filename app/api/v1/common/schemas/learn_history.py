from pydantic import BaseModel, Field
from typing import Literal, Optional, Union
from datetime import datetime
from decimal import Decimal

LearningMode = Literal["MJ", "JM"]

class LearnHistoryRequest(BaseModel):
    word_id: int
    level: int
    confidence: int = Field(description="Easiness level (0-3)")
    time: Decimal = Field(description="Time taken to answer in seconds")

class LearnHistoryResponse(BaseModel):
    user_id: Optional[str] = None
    word_id: int
    level: int
    proficiency_MJ: Decimal = Field(ge=0, le=1)
    proficiency_JM: Decimal = Field(ge=0, le=1)
    next_mode: Literal["MJ", "JM"]
    next_datetime: datetime

class NextWordRequest(BaseModel):
    level: Union[int, str] = Field(..., description="学習レベル（1-14）または'REVIEW_ALL'（全レベルから復習）")

class NextWordResponse(BaseModel):
    answer_word_id: int
    mode: LearningMode

class NoWordAvailableResponse(BaseModel):
    message: str = "現在学習可能な単語がありません"
    next_available_datetime: Optional[datetime] = None 