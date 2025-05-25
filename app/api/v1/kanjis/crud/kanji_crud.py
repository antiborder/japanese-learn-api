from sqlalchemy.orm import Session
from common.models.kanji_component import Kanji
from common.schemas.kanji_component import KanjiCreate
from common.models.word import Word
import logging

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_kanji(db: Session, kanji_id: int):
    # return kanji_service.get_kanji(db, kanji_id)    
    return db.query(Kanji).filter(Kanji.id == kanji_id).first()


def get_kanjis(db: Session):
    return db.query(Kanji).all()


def create_kanji(db: Session, kanji: KanjiCreate):
    try:
        db_kanji = Kanji(**kanji.dict())
        db.add(db_kanji)
        db.commit()
        db.refresh(db_kanji)
        return db_kanji
    except Exception as e:
        logger.error("Error saving kanji to database: %s", str(e))
        raise


def get_kanji_by_character(db: Session, character: str):
    return db.query(Kanji).filter(Kanji.character == character).first()


def get_words_by_kanji_id(db: Session, kanji_id: int):
    # kanji_idに対応するcharacterを取得
    kanji = db.query(Kanji).filter(Kanji.id == kanji_id).first()
    character = kanji.character
    
    # word.nameの文字列ががcharacterを含むものを取得
    return db.query(Word).filter(Word.name.like(f'%{character}%')).all()


def update_kanji(db: Session, existing_kanji: Kanji, kanji_data: dict):
    for key, value in kanji_data.items():
        setattr(existing_kanji, key, value)
    db.commit()  # 変更をコミット
    return existing_kanji