import json
import os
from urllib.parse import quote_plus
# app.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from sqlalchemy import create_engine, Column, Integer, String # type: ignore
from sqlalchemy.ext.declarative import declarative_base # type: ignore
from sqlalchemy.orm import sessionmaker # type: ignore
from sqlalchemy.orm import Session # type: ignore
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # すべてのオリジンを許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データベースのURLを設定
DATABASE_URL = "mysql+pymysql://dbmasteruser:D%<WBLKR9!,ZNT1gNzxIU#*,D_xU?48q@ls-c473c9825c62e9efe33c74c6f241de905c9d5e8d.cxcecqy6s31q.ap-northeast-1.rds.amazonaws.com:3306/japanese_learn"

# SQLAlchemyのエンジンを作成
engine = create_engine(DATABASE_URL)

# セッションを作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ベースクラスを作成
Base = declarative_base()

# データベースセッションを取得する関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"Hello": "World!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, db: Session = Depends(get_db)):
    # データベースからアイテムを取得するロジックを追加
    item = db.query(Item).filter(Item.id == item_id).first()
    return item.name

handler = Mangum(app)

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

# @app.on_event("startup")
# def startup():
#     Base.metadata.create_all(bind=engine)