from typing import Optional, List
from pydantic import BaseModel

class WordInSentence(BaseModel):
    word_id: Optional[int] = None
    word_name: str

    class Config:
        orm_mode = True

class Sentence(BaseModel):
    sentence_id: int
    japanese: str
    level: int
    english: Optional[str] = None
    vietnamese: Optional[str] = None
    chinese: Optional[str] = None
    korean: Optional[str] = None
    indonesian: Optional[str] = None
    hindi: Optional[str] = None
    hurigana: str  # huriganaフィールドを追加
    grammar_ids: List[int]
    words: List[WordInSentence]
    dummy_words: List[str]

    class Config:
        orm_mode = True

class SentenceCreate(Sentence):
    pass

class Sentences(BaseModel):
    sentences: List[Sentence]

    class Config:
        orm_mode = True

class SentenceGrammarDescription(BaseModel):
    sentence_id: int
    sentence_text: str
    jlpt_level: str
    language: str
    description: str

    class Config:
        orm_mode = True
