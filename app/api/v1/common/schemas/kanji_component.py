from typing import Optional, List
from pydantic import BaseModel


class KanjiBase(BaseModel):
    character: str
    english: Optional[str] = None
    vietnamese: Optional[str] = None
    strokes: Optional[int] = None
    onyomi: Optional[str] = None
    kunyomi: Optional[str] = None
    level: Optional[str] = None

    class Config:
        orm_mode = True


class ComponentBase(BaseModel):
    character: str
    name: Optional[str] = None
    en: Optional[str] = None
    vi: Optional[str] = None

    class Config:
        orm_mode = True


class KanjiCreate(KanjiBase):
    pass


class Kanji(KanjiBase):
    id: int
    components: Optional[List[ComponentBase]] = None


class ComponentCreate(ComponentBase):
    pass


class Component(ComponentBase):
    id: int
    kanjis: Optional[List[KanjiBase]] = None


class KanjiWord(BaseModel):
    id: int

    class Config:
        orm_mode = True


class PaginationInfo(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedKanjisResponse(BaseModel):
    data: List[Kanji]
    pagination: PaginationInfo