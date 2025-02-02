# from sqlalchemy.orm import Session
# from app.repository.kanji_repository import get_kanji_by_id
# from app.repository.component_repository import get_components_by_kanji_id
# from app.schemas.kanji_component import ComponentBase
# import logging

# # def get_kanji(db: Session, kanji_id: int):
# #     kanji = get_kanji_by_id(db, kanji_id)
# #     if kanji is None:
# #         return None
    
# #     components = get_components_by_kanji_id(db, kanji_id)
# #     kanji.components = [ComponentBase(**kanji.__dict__) for kanji in components] if components else []
# #     logging.info(f"kanji: {kanji}")
# #     return kanji