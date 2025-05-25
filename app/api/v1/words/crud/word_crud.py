from sqlalchemy.orm import Session
from common.models.word import Word
from common.schemas.word import WordCreate
from common.models.kanji_component import Kanji
import logging


# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_word(db: Session, word_id: int):
    return db.query(Word).filter(Word.id == word_id).first()


def get_words(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Word).offset(skip).limit(limit).all()


def create_word(db: Session, word: WordCreate):
    try:
        db_word = Word(**word.dict())
        db.add(db_word)
        db.commit()
        db.refresh(db_word)
        return db_word
    except Exception as e:
        logger.error("Error saving word to database: %s", str(e))  # エラーログ
        raise
