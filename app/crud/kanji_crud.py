from sqlalchemy.orm import Session
from app.models.kanji_component import Kanji
from app.schemas.kanji_component import KanjiCreate
from app.service import kanji_service


import logging
from sqlalchemy import text

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


from sqlalchemy.orm import Session

def get_kanji(db: Session, kanji_id: int):
    # return kanji_service.get_kanji(db, kanji_id)    
    return db.query(Kanji).filter(Kanji.id == kanji_id).first()

def get_kanjis(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Kanji).offset(skip).limit(limit).all()

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
    return db.query(Kanji).filter(Kanji.character == character).all()

def debug_kanji_component_connection(db: Session):
    try:
        # kanji_componentテーブルの内容を取得
        results = db.execute(text("SELECT * FROM kanji_component")).fetchall()
        
        if results:
            logger.info("kanji_componentテーブルのデータ:")
            for row in results:
                logger.info(row)
        else:
            logger.warning("kanji_componentテーブルは空です。")
    
    except Exception as e:
        logger.error("kanji_componentテーブルへの接続中にエラーが発生しました: %s", str(e))
