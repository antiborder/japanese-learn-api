from sqlalchemy.orm import Session
import csv
from io import StringIO
from app.models.kanji_component import Kanji, Component
from app.schemas.kanji_component import KanjiCreate, ComponentCreate
from app.crud import kanji_crud, component_crud
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


def import_kanjis_from_csv(file_contents: str, db: Session):
    decoded_contents = file_contents.decode("utf-8")
    csv_reader = csv.reader(StringIO(decoded_contents))

    # ヘッダーをスキップ
    next(csv_reader)

    for row in csv_reader:
        if len(row) < 7:  # 必要なカラム数を確認
            continue

        kanji_data = {
            "character": row[1],
            "english": row[2],
            "vietnamese": row[3],
            "strokes": int(row[4]) if row[4].isdigit() else None,
            "onyomi": row[5],
            "kunyomi": row[6],
        }

        # 既存のKanjiを取得
        existing_kanji = db.query(Kanji).filter(Kanji.character == kanji_data["character"]).first()

        if existing_kanji:
            # 既存のKanjiを更新
            for key, value in kanji_data.items():
                setattr(existing_kanji, key, value)
            db.commit()  # 変更をコミット

            # Componentsの処理
            components = row[7:]  # 7列目以降がcomponents
            for component_character in components:
                if component_character:  # 空でない場合のみ処理
                    # 既存のComponentを取得
                    existing_component = db.query(Component).filter(Component.character == component_character).first()
                    
                    if not existing_component:
                        # 新しいComponentを作成
                        component_create = ComponentCreate(character=component_character)
                        existing_component = component_crud.create_component(db=db, component=component_create)

                    # KanjiとComponentの関連付け
                    if existing_component not in existing_kanji.components:
                        existing_kanji.components.append(existing_component)
                        db.commit()  # kanji_componentテーブルに新しいレコードを作成するためにコミット
        else:
            # Kanjiの作成
            kanji_create = KanjiCreate(**kanji_data)
            created_kanji = kanji_crud.create_kanji(db=db, kanji=kanji_create)

            # Componentsの処理
            components = row[7:]  # 7列目以降がcomponents
            for component_character in components:
                if component_character:  # 空でない場合のみ処理
                    # 既存のComponentを取得
                    existing_component = db.query(Component).filter(Component.character == component_character).first()
                    
                    if not existing_component:
                        # 新しいComponentを作成
                        component_create = ComponentCreate(character=component_character)
                        existing_component = component_crud.create_component(db=db, component=component_create)

                    # KanjiとComponentの関連付け
                    created_kanji.components.append(existing_component)
                    db.commit()  # kanji_componentテーブルに新しいレコードを作成するためにコミット

    return {"message": "Kanjis and components imported successfully"}
