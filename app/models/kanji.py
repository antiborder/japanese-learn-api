from sqlalchemy import Column, Integer, String
from app.database import Base

class Kanji(Base):
    __tablename__ = "kanjis"

    id = Column(Integer, primary_key=True, index=True)
    character = Column(String(255), nullable=False)
    english = Column(String(255), nullable=True)
    vietnamese = Column(String(255), nullable=True)
    strokes = Column(Integer, nullable=True)  # 画数
    onyomi = Column(String(255), nullable=True)  # 音読み
    kunyomi = Column(String(255), nullable=True)  # 訓読み
    level = Column(String(50), nullable=True)  # 新しく追加したlevelフィールド