from typing import Optional, List
from pydantic import BaseModel

class Word(BaseModel):
    id: int
    name: str
    hiragana: str
    is_katakana: bool = False
    level: Optional[int] = None
    english: Optional[str] = None
    vietnamese: Optional[str] = None
    lexical_category: Optional[str] = None
    accent_up: Optional[int] = None
    accent_down: Optional[int] = None

    class Config:
        orm_mode = True

class WordCreate(Word):
    pass

class Words(BaseModel):
    words: List[Word]

    class Config:
        orm_mode = True

class WordKanji(BaseModel):
    id: int
    char: str

    class Config:
        orm_mode = True