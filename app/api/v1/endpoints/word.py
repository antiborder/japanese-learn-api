from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.crud import word as word_crud
from app.schemas.word import Word, WordCreate
from app.database import get_db
import logging
import traceback
from app.utils.utils import convert_hiragana_to_romaji

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/words", response_model=Word)
def create_word(word: WordCreate, db: Session = Depends(get_db)):
    try:
        return word_crud.create_word(db=db, word=word)
    except Exception as e:
        logger.error("Error creating word: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/words", response_model=List[Word])
def read_words(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        words = word_crud.get_words(db, skip=skip, limit=limit)
        
        # 各wordにromajiを追加
        for word in words:
            word.romaji = convert_hiragana_to_romaji(word.hiragana)
        
        return words
    except Exception as e:
        logger.error("Error reading words: %s", str(e))
        logger.error("Stack trace: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/words/{word_id}", response_model=Word)
def read_word(word_id: int, db: Session = Depends(get_db)):
    try:
        db_word = word_crud.get_word(db, word_id=word_id)
        if db_word is None:
            raise HTTPException(status_code=404, detail="Word not found")
        
        db_word.romaji = convert_hiragana_to_romaji(db_word.hiragana)
        
        return {
            "id": db_word.id,
            "name": db_word.name,
            "hiragana": db_word.hiragana,
            "romaji": db_word.romaji,
            "is_katakana": db_word.is_katakana,
            "level": db_word.level,
            "english": db_word.english,
            "vietnamese": db_word.vietnamese,
            "lexical_category": db_word.lexical_category,
            "accent_up": db_word.accent_up,
            "accent_down": db_word.accent_down,
        }
    except Exception as e:
        logger.error("Error reading word with ID %d: %s", word_id, str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")