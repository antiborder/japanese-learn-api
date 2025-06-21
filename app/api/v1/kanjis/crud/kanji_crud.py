from integrations.dynamodb_kanji import dynamodb_kanji_client
import logging

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_kanji(kanji_id: int):
    """
    DynamoDBから漢字情報を取得します。
    """
    return dynamodb_kanji_client.get_kanji_by_id(kanji_id)


def get_kanjis():
    """
    DynamoDBから全ての漢字情報を取得します。
    """
    return dynamodb_kanji_client.get_all_kanjis()


# def create_kanji(db: Session, kanji: KanjiCreate):
#     try:
#         db_kanji = Kanji(**kanji.dict())
#         db.add(db_kanji)
#         db.commit()
#         db.refresh(db_kanji)
#         return db_kanji
#     except Exception as e:
#         logger.error("Error saving kanji to database: %s", str(e))
#         raise


# def get_words_by_kanji_id(db: Session, kanji_id: int):
#     # kanji_idに対応するcharacterを取得
#     kanji = db.query(Kanji).filter(Kanji.id == kanji_id).first()
#     character = kanji.character
    
#     # word.nameの文字列ががcharacterを含むものを取得
#     return db.query(Word).filter(Word.name.like(f'%{character}%')).all()


# def update_kanji(db: Session, existing_kanji: Kanji, kanji_data: dict):
#     for key, value in kanji_data.items():
#         setattr(existing_kanji, key, value)
#     db.commit()  # 変更をコミット
#     return existing_kanji