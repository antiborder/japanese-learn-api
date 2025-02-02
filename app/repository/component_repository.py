# from sqlalchemy.orm import Session
# from app.models.kanji_component import Component, Kanji
# import logging

# def get_component_by_id(db: Session, component_id: int):
#     return db.query(Component).filter(Component.id == component_id).first()


# def get_components_by_kanji_id(db: Session, kanji_id: int):
#     return db.query(Component).join(Kanji.components).filter(Kanji.id == kanji_id).first()

# # def get_components_by_kanji_id(db: Session, kanji_id: int):
# #     components = db.query(Component).join(Kanji.components).filter(Kanji.id == kanji_id).all()
# #     # 戻り値をログ出力
# #     logging.info(f"components: {components}")
    
# #     # ComponentBase型のリストを返す
# #     return [
# #         ComponentBase(
# #             character=component.character,
# #             name=component.name,
# #             en=component.en,
# #             vi=component.vi
# #         ) for component in components
# #     ]
