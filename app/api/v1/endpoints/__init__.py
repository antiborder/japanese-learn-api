from fastapi import APIRouter
from . import word, kanji  # kanjiをインポート

router = APIRouter()
router.include_router(word.router, prefix="/words", tags=["words"])
router.include_router(kanji.router, prefix="/kanjis", tags=["kanjis"])  # kanjiルーターを追加