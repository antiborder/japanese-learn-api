from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import StreamingResponse
from app.crud import kanji_crud as kanji_crud
from app.service import kanji_service
from app.schemas.kanji_component import Kanji, KanjiCreate
from app.database import get_db
from app.crud import component_crud as component_crud
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/kanjis", response_model=Kanji)
def create_kanji(kanji: KanjiCreate, db: Session = Depends(get_db)):
    return kanji_crud.create_kanji(db=db, kanji=kanji)


@router.get("/kanjis", response_model=List[Kanji])
def read_kanjis(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return kanji_crud.get_kanjis(db, skip=skip, limit=limit)


@router.get("/kanjis/{kanji_id}", response_model=Kanji)
def read_kanji(kanji_id: int, db: Session = Depends(get_db)):
    kanji = kanji_crud.get_kanji(db, kanji_id=kanji_id)
    if kanji is None:
        raise HTTPException(status_code=404, detail="Kanji not found")
    return kanji


@router.get("/kanjis/character/{character}", response_model=Kanji)
def read_kanji_by_character(character: str, db: Session = Depends(get_db)):
    return kanji_crud.get_kanji_by_character(db, character=character)


@router.get("/kanjis/export/csv", response_class=StreamingResponse)
def export_kanjis_to_csv(db: Session = Depends(get_db)):
    output = kanji_service.generate_kanji_csv(db)  # kanji_serviceの関数を呼び出す
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=kanjis.csv"})


@router.post("/kanjis/import/csv")
async def import_kanjis_from_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = await file.read()
    return kanji_service.import_kanjis_from_csv(contents, db)