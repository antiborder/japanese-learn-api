from typing import Optional, List
from pydantic import BaseModel


class KanjiBase(BaseModel):
    id: Optional[int] = None
    character: str
    english: Optional[str] = None
    vietnamese: Optional[str] = None
    strokes: Optional[int] = None
    onyomi: Optional[str] = None
    kunyomi: Optional[str] = None

    class Config:
        orm_mode = True


class ComponentBase(BaseModel):
    id: Optional[int] = None
    character: Optional[str] = None
    name: Optional[str] = None
    en: Optional[str] = None
    vi: Optional[str] = None

    class Config:
        orm_mode = True


class KanjiCreate(KanjiBase):
    pass


class Kanji(KanjiBase):
    components: Optional[List[ComponentBase]]


class ComponentCreate(ComponentBase):
    pass


class Component(ComponentBase):
    kanjis: Optional[List[KanjiBase]]