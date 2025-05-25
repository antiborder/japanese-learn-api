from sqlalchemy import Column, Integer, String, Boolean
from ..database import Base

class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    hiragana = Column(String(255))
    is_katakana = Column(Boolean, default=False)
    level = Column(Integer)
    english = Column(String(255))
    vietnamese = Column(String(255))
    lexical_category = Column(String(50))
    accent_up = Column(Integer)
    accent_down = Column(Integer) 