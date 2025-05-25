from fastapi import APIRouter, Depends, HTTPException # , UploadFile, File
from sqlalchemy.orm import Session
from typing import List
# from fastapi.responses import StreamingResponse
from crud import word_crud
from crud.word_crud import get_kanji_by_character
from common.schemas.word import Word, WordCreate
from common.schemas.kanji_component import Kanji
from common.utils.utils import convert_hiragana_to_romaji
from services.word_service import get_audio_url
from common.database import get_db # , Base
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=Word)
def create_word(word: WordCreate, db: Session = Depends(get_db)):
    try:
        return word_crud.create_word(db=db, word=word)
    except Exception as e:
        logger.error(f"Error creating word: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/", response_model=List[Word])
def read_words(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        return word_crud.get_words(db=db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error reading words: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/character/{character}/kanji", response_model=Kanji)
def read_kanji_by_character(character: str, db: Session = Depends(get_db)):
    try:
        kanji = get_kanji_by_character(db, character=character)
        if kanji is None:
            raise HTTPException(status_code=404, detail="Kanji not found")
        return kanji
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error reading kanji by character {character}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
        

@router.get("/{word_id}", response_model=Word)
def read_word(word_id: int, db: Session = Depends(get_db)):
    try:
        word = word_crud.get_word(db, word_id=word_id)
        if word is None:
            raise HTTPException(status_code=404, detail="Word not found")
        
        word.romaji = convert_hiragana_to_romaji(word.hiragana)
        return word
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error reading word {word_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{word_id}/audio_url", response_model=dict)
async def fetch_word_audio(word_id: int, db: Session = Depends(get_db)):
    try:
        logger.info(f"Fetching audio URL for word_id: {word_id}")
        audio_url = get_audio_url(word_id, db)
        return {
            "url": audio_url,
            "expires_in": 3600
        }
    except Exception as e:
        logger.error(f"Error fetching audio URL for word_id {word_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))