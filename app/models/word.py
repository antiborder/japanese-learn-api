from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)    
    hiragana = Column(String(255), nullable=False)
    is_katakana = Column(Boolean, default=False)
    level = Column(String(50), nullable=True)
    english = Column(String(255), nullable=True)
    vietnamese = Column(String(255), nullable=True)
    lexical_category = Column(String(50), nullable=True)
    accent_up = Column(Integer, nullable=True)
    accent_down = Column(Integer, nullable=True)