from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.crud import word as word_crud
from app.schemas.word import Word, WordCreate
from app.database import get_db

router = APIRouter()

@router.post("/words/", response_model=Word)
def create_word(word: WordCreate, db: Session = Depends(get_db)):
    return word_crud.create_word(db=db, word=word)

@router.get("/words/", response_model=List[Word])
def read_words(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    words = word_crud.get_words(db, skip=skip, limit=limit)
    return words

@router.get("/words/{word_id}", response_model=Word)
def read_word(word_id: int, db: Session = Depends(get_db)):
    db_word = word_crud.get_word(db, word_id=word_id)
    if db_word is None:
        raise HTTPException(status_code=404, detail="Word not found")
    return db_word