from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime
from decimal import Decimal

LearningMode = Literal["MJ", "JM"]

class LearnHistoryRequest(BaseModel):
    user_id: Optional[str] = None
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
    user_id: str
    level: int

class NextWordResponse(BaseModel):
    answer_word_id: int
    mode: LearningMode 