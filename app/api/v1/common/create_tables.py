from database import Base, engine
from models.kanji_component import Kanji, Component, kanji_components
from models.word import Word

def create_tables():
    # 全てのテーブルを作成
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()
    print("テーブルが作成されました。") 