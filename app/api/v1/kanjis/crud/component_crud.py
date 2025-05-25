from sqlalchemy.orm import Session
from common.models.kanji_component import Component
from common.schemas.kanji_component import ComponentCreate
import logging

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_components(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Component).offset(skip).limit(limit).all()


def get_component(db: Session, component_id: int):
    return db.query(Component).filter(Component.id == component_id).first() 


def create_component(db: Session, component: ComponentCreate):
    db_component = Component(**component.dict())
    db.add(db_component)
    db.commit()
    db.refresh(db_component)
    return db_component

def get_component_by_character(db: Session, character: str):
    return db.query(Component).filter(Component.character == character).first()

def update_component(db: Session, existing_component: Component, component_data: dict):
    for key, value in component_data.items():
        setattr(existing_component, key, value)
    db.commit()  # 変更をコミット
    return existing_component

def relate_component_to_kanji(db: Session, kanji, component):
    kanji.components.append(component)
    db.commit()

