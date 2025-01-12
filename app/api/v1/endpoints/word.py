from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.crud import word as word_crud
from app.schemas.word import Word, WordCreate
from app.database import get_db
import logging
import traceback

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/words", response_model=Word)
def create_word(word: WordCreate, db: Session = Depends(get_db)):
    try:
        logger.info("Creating a new word: %s", word)  # INFOログ
        return word_crud.create_word(db=db, word=word)
    except Exception as e:
        logger.error("Error creating word: %s", str(e))  # エラーログ
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/words", response_model=List[Word])
def read_words(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        logger.info("Fetching words with skip=%d and limit=%d", skip, limit)  # INFOログ
        words = word_crud.get_words(db, skip=skip, limit=limit)
        if not words:  # 空リストの場合
            logger.warning("No words found")  # 警告ログ
            raise HTTPException(status_code=404, detail="No words found")
        logger.info("Fetched %d words", len(words))  # INFOログ
        return words
    except Exception as e:
        logger.error("Error reading words: %s", str(e))  # エラーログ
        logger.error("Stack trace: %s", traceback.format_exc())  # スタックトレースをログに出力
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/words/{word_id}", response_model=Word)
def read_word(word_id: int, db: Session = Depends(get_db)):
    try:
        logger.info("Fetching word with ID: %d", word_id)  # INFOログ
        db_word = word_crud.get_word(db, word_id=word_id)
        if db_word is None:
            logger.warning("Word with ID %d not found", word_id)  # 警告ログ
            raise HTTPException(status_code=404, detail="Word not found")
        logger.info("Fetched word: %s", db_word)  # INFOログ
        return db_word
    except Exception as e:
        logger.error("Error reading word with ID %d: %s", word_id, str(e))  # エラーログ
        raise HTTPException(status_code=500, detail="Internal Server Error")