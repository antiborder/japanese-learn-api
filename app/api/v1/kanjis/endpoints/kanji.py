from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import StreamingResponse
from crud.kanji_crud import get_kanji, get_kanjis, create_kanji, get_words_by_kanji_id
from services.kanji_service import generate_kanji_csv, import_kanjis_from_csv
from common.schemas.kanji_component import Kanji, KanjiCreate
from common.database import get_db
from common.schemas.word import Word
import logging
from pydantic import BaseModel

class KanjiIdResponse(BaseModel):
    kanji_id: int

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=Kanji)
def create_kanji_endpoint(kanji: KanjiCreate, db: Session = Depends(get_db)):
    try:
        return create_kanji(db=db, kanji=kanji)
    except Exception as e:
        logger.error(f"Error creating kanji: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/", response_model=List[Kanji])
def read_kanjis_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        return get_kanjis(db)
    except Exception as e:
        logger.error(f"Error reading kanjis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{kanji_id}", response_model=Kanji)
def read_kanji(kanji_id: int, db: Session = Depends(get_db)):
    try:
        kanji = get_kanji(db, kanji_id=kanji_id)
        if kanji is None:
            raise HTTPException(status_code=404, detail="Kanji not found")
        return kanji
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error reading kanji {kanji_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{kanji_id}/words", response_model=List[Word])
def read_words_by_kanji_id(kanji_id: int, db: Session = Depends(get_db)):
    try:
        return get_words_by_kanji_id(db, kanji_id=kanji_id)
    except Exception as e:
        logger.error(f"Error reading words for kanji {kanji_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/export/csv", response_class=StreamingResponse)
def export_kanjis_to_csv(db: Session = Depends(get_db)):
    try:
        output = generate_kanji_csv(db)
        return StreamingResponse(
            output, 
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=kanjis.csv"}
        )
    except Exception as e:
        logger.error(f"Error exporting kanjis to CSV: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/import/csv")
async def import_kanjis_from_csv_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        return import_kanjis_from_csv(contents, db)
    except Exception as e:
        logger.error(f"Error importing kanjis from CSV: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")