from typing import Optional
from pydantic import BaseModel

class KanjiBase(BaseModel):
    character: str
    english: Optional[str] = None
    vietnamese: Optional[str] = None
    strokes: Optional[int] = None
    onyomi: Optional[str] = None
    kunyomi: Optional[str] = None

class KanjiCreate(KanjiBase):
    pass

class Kanji(KanjiBase):
    id: int

    class Config:
        orm_mode = True