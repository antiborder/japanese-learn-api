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
    limit: int
    has_next: bool
    next_cursor: Optional[str] = None
    # 以下は後方互換のために残しているが、カーソルベースのページネーションに
    # 移行したため正確な値ではない（algorithm上、全件スキャンなしに正確な値を
    # 算出できないため）。ページ送りには has_next / next_cursor を使うこと。
    page: Optional[int] = None
    total: Optional[int] = None
    total_pages: Optional[int] = None
    has_previous: Optional[bool] = None


class PaginatedKanjisResponse(BaseModel):
    data: List[Kanji]
    pagination: PaginationInfo
