from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.crud import kanji as kanji_crud
from app.schemas.kanji import Kanji, KanjiCreate
from app.database import get_db

router = APIRouter()

@router.post("/kanjis", response_model=Kanji)
def create_kanji(kanji: KanjiCreate, db: Session = Depends(get_db)):
    return kanji_crud.create_kanji(db=db, kanji=kanji)

@router.get("/kanjis", response_model=List[Kanji])
def read_kanjis(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return kanji_crud.get_kanjis(db, skip=skip, limit=limit)

@router.get("/kanjis/{kanji_id}", response_model=Kanji)
def read_kanji(kanji_id: int, db: Session = Depends(get_db)):
    return kanji_crud.get_kanji(db, kanji_id=kanji_id)

@router.get("/kanjis/character/{character}", response_model=List[Kanji])
def read_kanji_by_character(character: str, db: Session = Depends(get_db)):
    return kanji_crud.get_kanji_by_character(db, character=character)