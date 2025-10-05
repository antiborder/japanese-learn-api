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
    english: str
    vietnamese: str
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
