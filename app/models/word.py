from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)    
    hiragana = Column(String(255), nullable=False)
    romanian = Column(String(255))
    is_katakana = Column(Boolean, default=False)
    level = Column(String(50))
    english = Column(String(255))
    vietnamese = Column(String(255))
    lexical_category = Column(String(50))
    accent_up = Column(Integer)
    accent_down = Column(Integer)

# データベースのエンジンを作成
engine = create_engine('sqlite:///your_database.db')  # 適切なデータベースURLに変更してください
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# テーブルを作成
Base.metadata.create_all(bind=engine)