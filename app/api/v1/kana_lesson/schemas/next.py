from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class KanaChar(BaseModel):
    char: str = Field(..., description="かな文字")
    level: int = Field(..., description="レベル")


class KanaNextResponse(BaseModel):
    answer_char: KanaChar


class NoKanaAvailableResponse(BaseModel):
    message: str = "現在学習可能なかなはありません"
    no_char_available: bool = True
    next_available_datetime: Optional[datetime] = None

