from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional, List
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

class WordInSentence(BaseModel):
    word_name: str
    word_id: Optional[int] = None

class SentenceResponse(BaseModel):
    sentence_id: int
    japanese: str
    level: int
    hurigana: str
    english: str
    vietnamese: str
    grammar_ids: List[int]
    words: List[WordInSentence]
    dummy_words: List[str]

class NoSentenceAvailableResponse(BaseModel):
    message: str = "現在学習可能な文がありません"
    no_sentence_available: bool = True
    next_available_datetime: Optional[datetime] = None
