from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator


class KanaAttemptRequest(BaseModel):
    char: str = Field(..., min_length=1, description="学習したかな文字")
    level: int = Field(..., description="学習レベル")
    confidence: int = Field(..., ge=0, le=3, description="自信度（0-3）")
    time: Decimal = Field(..., ge=0, description="回答に要した時間（秒）")

    @validator("char")
    def validate_single_character(cls, value: str) -> str:
        if len(value) != 1:
            raise ValueError("char は1文字である必要があります")
        return value


class KanaAttemptResponse(BaseModel):
    user_id: str
    char: str
    level: int
    proficiency: Decimal = Field(ge=0, le=1)
    next_datetime: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
