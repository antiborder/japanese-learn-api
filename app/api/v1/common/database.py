from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.error(f"データベース接続エラー: {str(e)}")
    raise

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"データベースセッションエラー: {str(e)}")
        raise
    finally:
        db.close() 