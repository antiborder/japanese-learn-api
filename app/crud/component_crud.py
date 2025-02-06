from sqlalchemy.orm import Session
from app.models.kanji_component import Component
from app.schemas.kanji_component import ComponentCreate
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
