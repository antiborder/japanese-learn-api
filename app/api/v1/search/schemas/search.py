from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class Language(str, Enum):
    EN = "en"
    VI = "vi"
    ZH_HANS = "zh-Hans"
    KO = "ko"
    ID = "id"
    HI = "hi"


class WordSearchResult(BaseModel):
    id: int
    name: str
    hiragana: str
    english: Optional[str] = None
    vietnamese: Optional[str] = None
    chinese: Optional[str] = None
    korean: Optional[str] = None
    indonesian: Optional[str] = None
    hindi: Optional[str] = None
    audio_url: Optional[str] = None


class KanjiSearchResult(BaseModel):
    id: int
    character: str
    english: Optional[str] = None
    vietnamese: Optional[str] = None
    strokes: Optional[int] = None
    onyomi: Optional[str] = None
    kunyomi: Optional[str] = None
    level: Optional[int] = None


class ComponentSearchResult(BaseModel):
    id: int
    character: str


class SearchResponse(BaseModel):
    words: List[WordSearchResult]
    kanjis: List[KanjiSearchResult]
    components: List[ComponentSearchResult]
    total_count: int
    query: str
    language: Language


class SearchRequest(BaseModel):
    query: str
    language: Language
    limit: Optional[int] = 20
    offset: Optional[int] = 0
