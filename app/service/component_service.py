from sqlalchemy.orm import Session
from app.repository.component_repository import get_component_by_id
from app.repository.kanji_repository import get_kanjis_by_component_id
from app.schemas.kanji_component import KanjiBase


# def get_component(db: Session, component_id: int):
#     component = get_component_by_id(db, component_id)
#     if component is None:
#         return None
    
#     kanjis = get_kanjis_by_component_id(db, component_id)
#     component.kanjis = [KanjiBase(**kanji.__dict__) for kanji in kanjis] if kanjis else []

#     return component