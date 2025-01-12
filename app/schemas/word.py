from typing import Optional
from pydantic import BaseModel

class WordBase(BaseModel):
    name: Optional[str] = None
    romanian: Optional[str] = None
    is_katakana: bool = False
    level: Optional[str] = None
    english: Optional[str] = None
    vietnamese: Optional[str] = None
    lexical_category: Optional[str] = None
    accent_up: Optional[int] = None
    accent_down: Optional[int] = None

class WordCreate(WordBase):
    pass

class Word(WordBase):
    id: int

    class Config:
        orm_mode = True