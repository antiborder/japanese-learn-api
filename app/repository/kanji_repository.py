# from sqlalchemy.orm import Session
# from app.models.kanji_component import Kanji, Component


# def get_kanjis(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(Kanji).offset(skip).limit(limit).all()


# def get_kanji_by_id(db: Session, kanji_id: int):
#     return db.query(Kanji).filter(Kanji.id == kanji_id).first()


# def get_kanjis_by_component_id(db: Session, component_id: int):
#     return db.query(Kanji).join(Component.kanjis).filter(Component.id == component_id).first()