from typing import Optional, List
from pydantic import BaseModel
from common.schemas.kanji_component import KanjiBase


class ComponentBase(BaseModel):
    character: Optional[str] = None
    name: Optional[str] = None
    en: Optional[str] = None
    vi: Optional[str] = None


class ComponentCreate(ComponentBase):
    pass


class Component(ComponentBase):
    id: str
    kanjis: Optional[List[KanjiBase]]

    class Config:
        orm_mode = True


class PaginationInfo(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedComponentsResponse(BaseModel):
    data: List[Component]
    pagination: PaginationInfo