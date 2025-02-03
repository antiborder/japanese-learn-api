from sqlalchemy.orm import Session
import csv
from io import StringIO
from app.models.kanji_component import Kanji
from dotenv import load_dotenv
import os

load_dotenv()

MAX_COMPONENT_COUNT = int(os.getenv("MAX_COMPONENT_COUNT"))


def generate_kanji_csv(db: Session):
    kanjis = db.query(Kanji).all()

    # CSVデータを生成
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Character", "English", "Vietnamese", "Strokes", "Onyomi", "Kunyomi"] + ["Component"] * MAX_COMPONENT_COUNT)  # ヘッダー行

    for kanji in kanjis:
        components = [component.name for component in kanji.components]
        components += [''] * (MAX_COMPONENT_COUNT - len(components))
        writer.writerow([
            kanji.id,
            kanji.character,
            kanji.english,
            kanji.vietnamese,
            kanji.strokes,
            kanji.onyomi,
            kanji.kunyomi,
        ] + components)  # componentsの情報を追加

    output.seek(0)  # StringIOのポインタを先頭に戻す
    return output
