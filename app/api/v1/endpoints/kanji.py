from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.crud import kanji_crud as kanji_crud
from app.schemas.kanji_component import Kanji, KanjiCreate
from app.database import get_db
# from app.service import kanji as kanji_service

router = APIRouter()

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

@router.get("/kanjis/character/{character}", response_model=List[Kanji])
def read_kanji_by_character(character: str, db: Session = Depends(get_db)):
    return kanji_crud.get_kanji_by_character(db, character=character)

# 例: エンドポイント内で呼び出す
@router.get("/debug/kanji_component")
def debug_kanji_component(db: Session = Depends(get_db)):
    kanji_crud.debug_kanji_component_connection(db)
    return {"message": "デバッグ情報がログに出力されました。"}