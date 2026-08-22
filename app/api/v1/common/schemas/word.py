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
    chinese: Optional[str] = None
    korean: Optional[str] = None
    indonesian: Optional[str] = None
    hindi: Optional[str] = None
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


class PaginatedWordsResponse(BaseModel):
    data: List[Word]
    pagination: PaginationInfo
