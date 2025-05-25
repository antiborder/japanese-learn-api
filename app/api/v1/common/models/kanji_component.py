from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

# 漢字と部首の多対多の関連を表すテーブル
class KanjiComponent(Base):
    __tablename__ = 'kanji_component'

    id = Column(Integer, primary_key=True, autoincrement=True)
    kanji_id = Column(Integer, ForeignKey('kanjis.id'))
    component_id = Column(Integer, ForeignKey('components.id'))

class Kanji(Base):
    __tablename__ = "kanjis"

    id = Column(Integer, primary_key=True, index=True)
    character = Column(String(255), nullable=False, index=True)
    english = Column(String(255))
    vietnamese = Column(String(255))
    strokes = Column(Integer)
    onyomi = Column(String(255))
    kunyomi = Column(String(255))
    level = Column(String(50))  # 新しく追加

    # 部首との関連
    components = relationship("Component", 
                            secondary="kanji_component",
                            back_populates="kanjis",
                            viewonly=True)

class Component(Base):
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, index=True)
    character = Column(String(10), unique=True, index=True)
    name = Column(String(255))
    en = Column(String(255))
    vi = Column(String(255))

    # 漢字との関連
    kanjis = relationship("Kanji", 
                         secondary="kanji_component",
                         back_populates="components",
                         viewonly=True) 