from sqlalchemy.orm import Session
import csv
from io import StringIO
from app.schemas.kanji_component import KanjiCreate, ComponentCreate
from app.crud import kanji_crud, component_crud
from dotenv import load_dotenv
import os

load_dotenv()

MAX_COMPONENT_COUNT = int(os.getenv("MAX_COMPONENT_COUNT"))
MIN_COLUMN_COUNT = int(os.getenv("MIN_COLUMN_COUNT"))


def write_kanji_to_csv(writer, kanji, max_component_count):
    components = [component.character for component in kanji.components]
    components += [''] * (max_component_count - len(components))
    print(components)
    writer.writerow([
        kanji.id,
        kanji.character,
        kanji.english,
        kanji.vietnamese,
        kanji.strokes,
        kanji.onyomi,
        kanji.kunyomi,
    ] + components)  # componentsの情報を追加


def generate_kanji_csv(db: Session):
    kanjis = kanji_crud.get_kanjis(db)
    print(kanjis)
    # CSVデータを生成
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Character", "English", "Vietnamese", "Strokes", "Onyomi", "Kunyomi"] + ["Component"] * MAX_COMPONENT_COUNT)  # ヘッダー行

    for kanji in kanjis:
        write_kanji_to_csv(writer, kanji, MAX_COMPONENT_COUNT)  # 新しい関数を呼び出す

    output.seek(0)  # StringIOのポインタを先頭に戻す
    return output


def get_kanji_data(row: list):
    kanji_data = {
        "character": row[1],
        "english": row[2],
        "vietnamese": row[3],
        "strokes": int(row[4]) if row[4].isdigit() else None,
        "onyomi": row[5],
        "kunyomi": row[6],
    }
    return kanji_data


def process_components(db: Session, kanji, components: list):
    for component_character in components:
        if not component_character:  # 空の場合は早期リターン
            continue

        existing_component = component_crud.get_component_by_character(db, component_character)
        
        if not existing_component:
            component_create = ComponentCreate(character=component_character)
            existing_component = component_crud.create_component(db=db, component=component_create)

        # KanjiとComponentの関連付け
        if existing_component not in kanji.components:
            component_crud.relate_component_to_kanji(db, kanji, existing_component)


def import_kanji_row(row: list, db: Session):
    if len(row) < MIN_COLUMN_COUNT:  # 必要なカラム数を確認
        return None

    kanji_data = get_kanji_data(row)
    existing_kanji = kanji_crud.get_kanji_by_character(db, kanji_data["character"])

    if existing_kanji:
        targeted_kanji = kanji_crud.update_kanji(db, existing_kanji, kanji_data)
    else:
        kanji_create = KanjiCreate(**kanji_data)
        targeted_kanji = kanji_crud.create_kanji(db=db, kanji=kanji_create)

    components = row[MIN_COLUMN_COUNT:]  # components列
    process_components(db, targeted_kanji, components)

    return {"kanji": targeted_kanji}


def import_kanjis_from_csv(file_contents: str, db: Session):
    decoded_contents = file_contents.decode("utf-8")
    csv_reader = csv.reader(StringIO(decoded_contents))

    # ヘッダーをスキップ
    next(csv_reader)

    for row in csv_reader:
        import_kanji_row(row, db)  # 新しい関数を呼び出す

    return {"message": "Kanjis and components imported successfully"}