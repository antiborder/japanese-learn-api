from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class Language(str, Enum):
    EN = "en"
    VI = "vi"


class WordSearchResult(BaseModel):
    id: int
    name: str
    hiragana: str
    english: Optional[str] = None
    vietnamese: Optional[str] = None
    audio_url: Optional[str] = None


class SearchResponse(BaseModel):
    words: List[WordSearchResult]
    total_count: int
    query: str
    language: Language


class SearchRequest(BaseModel):
    query: str
    language: Language
    limit: Optional[int] = 20
    offset: Optional[int] = 0
