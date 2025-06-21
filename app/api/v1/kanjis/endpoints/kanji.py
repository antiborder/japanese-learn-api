from fastapi import APIRouter, HTTPException
from typing import List
from common.schemas.kanji_component import Kanji
from crud.kanji_crud import get_kanji, get_kanjis
import logging
from pydantic import BaseModel
from integrations.dynamodb_kanji import dynamodb_kanji_client

class KanjiIdResponse(BaseModel):
    kanji_id: int

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[Kanji])
def read_kanjis_endpoint(skip: int = 0, limit: int = 100):
    try:
        return get_kanjis()
    except Exception as e:
        logger.error(f"Error reading kanjis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{kanji_id}", response_model=Kanji)
def read_kanji(kanji_id: int):
    try:
        kanji = get_kanji(kanji_id=kanji_id)
        if kanji is None:
            raise HTTPException(status_code=404, detail="Kanji not found")
        return kanji
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error reading kanji {kanji_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{kanji_id}/components", response_model=List[dict])
def get_components_by_kanji_id(kanji_id: str):
    try:
        return dynamodb_kanji_client.get_components_by_kanji_id(str(kanji_id))
    except Exception as e:
        logger.error(f"Error getting components for kanji {kanji_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")