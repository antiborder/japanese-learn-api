from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Kanji(Base):
    __tablename__ = "kanjis"

    id = Column(Integer, primary_key=True, index=True)
    character = Column(String(255), nullable=False)
    english = Column(String(255), nullable=True)
    vietnamese = Column(String(255), nullable=True)
    strokes = Column(Integer, nullable=True)
    onyomi = Column(String(255), nullable=True)
    kunyomi = Column(String(255), nullable=True)
    level = Column(String(50), nullable=True)

    components = relationship("Component", secondary="kanji_component", back_populates="kanjis", overlaps="kanjis")
    kanji_component = relationship("KanjiComponent", back_populates="kanji")


class Component(Base):
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, index=True)
    character = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    en = Column(String(255), nullable=True)
    vi = Column(String(255), nullable=True)

    kanjis = relationship("Kanji", secondary="kanji_component", back_populates="components", overlaps="components")
    kanji_component = relationship("KanjiComponent", back_populates="component")


class KanjiComponent(Base):
    __tablename__ = "kanji_component"

    kanji_id = Column(Integer, ForeignKey("kanjis.id"), primary_key=True)
    component_id = Column(Integer, ForeignKey("components.id"), primary_key=True)
    
    kanji = relationship("Kanji", back_populates="kanji_component", overlaps="kanjis")
    component = relationship("Component", back_populates="kanji_component", overlaps="components")