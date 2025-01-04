from sqlalchemy.orm import Session
from app.models.word import Word
from app.schemas.word import WordCreate

def get_word(db: Session, word_id: int):
    return db.query(Word).filter(Word.id == word_id).first()

def get_words(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Word).offset(skip).limit(limit).all()

def create_word(db: Session, word: WordCreate):
    db_word = Word(**word.dict())
    db.add(db_word)
    db.commit()
    db.refresh(db_word)
    return db_word