from pydantic import BaseModel

class WordBase(BaseModel):
    name: str | None = None
    hiragana: str
    romanian: str | None = None
    is_katakana: bool = False
    level: str | None = None
    english: str | None = None
    vietnamese: str | None = None
    lexical_category: str | None = None
    accent_up: int | None = None
    accent_down: int | None = None

class WordCreate(WordBase):
    pass

class Word(WordBase):
    id: int

    class Config:
        orm_mode = True