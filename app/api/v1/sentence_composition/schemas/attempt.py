from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from datetime import datetime

class SentenceAttemptRequest(BaseModel):
    sentence_id: int
    level: int
    confidence: int = Field(description="Easiness level (0-3)")
    time: Decimal = Field(description="Time taken to answer in seconds")

class SentenceAttemptResponse(BaseModel):
    user_id: str
    sentence_id: int
    level: int
    proficiency: Decimal
    next_datetime: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
