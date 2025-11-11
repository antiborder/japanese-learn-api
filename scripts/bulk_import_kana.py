import boto3
from decimal import Decimal

TABLE_NAME = "japanese-learn-table"  # ← 実際の DynamoDB テーブル名に置き換えてください

HIRAGANA_LEVEL = -10
KATAKANA_LEVEL = -7

HIRAGANA_DATA = [
    {"character": "あ", "consonant": None, "vowel": "a",  "row_number": 1,  "column_number": 1,  "sub_level": 1},
    {"character": "い", "consonant": None, "vowel": "i",  "row_number": 1,  "column_number": 2,  "sub_level": 1},
    {"character": "う", "consonant": None, "vowel": "u",  "row_number": 1,  "column_number": 3,  "sub_level": 1},
    {"character": "え", "consonant": None, "vowel": "e",  "row_number": 1,  "column_number": 4,  "sub_level": 1},
    {"character": "お", "consonant": None, "vowel": "o",  "row_number": 1,  "column_number": 5,  "sub_level": 1},
    {"character": "か", "consonant": "k",  "vowel": "a",  "row_number": 2,  "column_number": 1,  "sub_level": 1},
    {"character": "き", "consonant": "k",  "vowel": "i",  "row_number": 2,  "column_number": 2,  "sub_level": 1},
    {"character": "く", "consonant": "k",  "vowel": "u",  "row_number": 2,  "column_number": 3,  "sub_level": 1},
    {"character": "け", "consonant": "k",  "vowel": "e",  "row_number": 2,  "column_number": 4,  "sub_level": 1},
    {"character": "こ", "consonant": "k",  "vowel": "o",  "row_number": 2,  "column_number": 5,  "sub_level": 1},
    {"character": "さ", "consonant": "s",  "vowel": "a",  "row_number": 3,  "column_number": 1,  "sub_level": 1},
    {"character": "し", "consonant": "sh", "vowel": "i",  "row_number": 3,  "column_number": 2,  "sub_level": 1},
    {"character": "す", "consonant": "s",  "vowel": "u",  "row_number": 3,  "column_number": 3,  "sub_level": 1},
    {"character": "せ", "consonant": "s",  "vowel": "e",  "row_number": 3,  "column_number": 4,  "sub_level": 1},
    {"character": "そ", "consonant": "s",  "vowel": "o",  "row_number": 3,  "column_number": 5,  "sub_level": 1},
    {"character": "た", "consonant": "t",  "vowel": "a",  "row_number": 4,  "column_number": 1,  "sub_level": 1},
    {"character": "ち", "consonant": "ch", "vowel": "i",  "row_number": 4,  "column_number": 2,  "sub_level": 1},
    {"character": "つ", "consonant": "ts", "vowel": "u",  "row_number": 4,  "column_number": 3,  "sub_level": 1},
    {"character": "て", "consonant": "t",  "vowel": "e",  "row_number": 4,  "column_number": 4,  "sub_level": 1},
    {"character": "と", "consonant": "t",  "vowel": "o",  "row_number": 4,  "column_number": 5,  "sub_level": 1},
    {"character": "な", "consonant": "n",  "vowel": "a",  "row_number": 5,  "column_number": 1,  "sub_level": 1},
    {"character": "に", "consonant": "n",  "vowel": "i",  "row_number": 5,  "column_number": 2,  "sub_level": 1},
    {"character": "ぬ", "consonant": "n",  "vowel": "u",  "row_number": 5,  "column_number": 3,  "sub_level": 1},
    {"character": "ね", "consonant": "n",  "vowel": "e",  "row_number": 5,  "column_number": 4,  "sub_level": 1},
    {"character": "の", "consonant": "n",  "vowel": "o",  "row_number": 5,  "column_number": 5,  "sub_level": 1},
    {"character": "は", "consonant": "h",  "vowel": "a",  "row_number": 6,  "column_number": 1,  "sub_level": 1},
    {"character": "ひ", "consonant": "h",  "vowel": "i",  "row_number": 6,  "column_number": 2,  "sub_level": 1},
    {"character": "ふ", "consonant": "f",  "vowel": "u",  "row_number": 6,  "column_number": 3,  "sub_level": 1},
    {"character": "へ", "consonant": "h",  "vowel": "e",  "row_number": 6,  "column_number": 4,  "sub_level": 1},
    {"character": "ほ", "consonant": "h",  "vowel": "o",  "row_number": 6,  "column_number": 5,  "sub_level": 1},
    {"character": "ま", "consonant": "m",  "vowel": "a",  "row_number": 7,  "column_number": 1,  "sub_level": 1},
    {"character": "み", "consonant": "m",  "vowel": "i",  "row_number": 7,  "column_number": 2,  "sub_level": 1},
    {"character": "む", "consonant": "m",  "vowel": "u",  "row_number": 7,  "column_number": 3,  "sub_level": 1},
    {"character": "め", "consonant": "m",  "vowel": "e",  "row_number": 7,  "column_number": 4,  "sub_level": 1},
    {"character": "も", "consonant": "m",  "vowel": "o",  "row_number": 7,  "column_number": 5,  "sub_level": 1},
    {"character": "や", "consonant": "y",  "vowel": "a",  "row_number": 8,  "column_number": 1,  "sub_level": 1},
    {"character": "ゆ", "consonant": "y",  "vowel": "u",  "row_number": 8,  "column_number": 3,  "sub_level": 1},
    {"character": "よ", "consonant": "y",  "vowel": "o",  "row_number": 8,  "column_number": 5,  "sub_level": 1},
    {"character": "ら", "consonant": "r",  "vowel": "a",  "row_number": 9,  "column_number": 1,  "sub_level": 1},
    {"character": "り", "consonant": "r",  "vowel": "i",  "row_number": 9,  "column_number": 2,  "sub_level": 1},
    {"character": "る", "consonant": "r",  "vowel": "u",  "row_number": 9,  "column_number": 3,  "sub_level": 1},
    {"character": "れ", "consonant": "r",  "vowel": "e",  "row_number": 9,  "column_number": 4,  "sub_level": 1},
    {"character": "ろ", "consonant": "r",  "vowel": "o",  "row_number": 9,  "column_number": 5,  "sub_level": 1},
    {"character": "わ", "consonant": "w",  "vowel": "a",  "row_number": 10, "column_number": 1,  "sub_level": 1},
    {"character": "を", "consonant": "w",  "vowel": "o",  "row_number": 10, "column_number": 5,  "sub_level": 1},
    {"character": "ん", "consonant": "n",  "vowel": None, "row_number": 11, "column_number": None, "sub_level": 1},
]

KATAKANA_DATA = [
    {"character": "ア", "consonant": None, "vowel": "a",  "row_number": 1,  "column_number": 1,  "sub_level": 1},
    {"character": "イ", "consonant": None, "vowel": "i",  "row_number": 1,  "column_number": 2,  "sub_level": 1},
    {"character": "ウ", "consonant": None, "vowel": "u",  "row_number": 1,  "column_number": 3,  "sub_level": 1},
    {"character": "エ", "consonant": None, "vowel": "e",  "row_number": 1,  "column_number": 4,  "sub_level": 1},
    {"character": "オ", "consonant": None, "vowel": "o",  "row_number": 1,  "column_number": 5,  "sub_level": 1},
    {"character": "カ", "consonant": "k",  "vowel": "a",  "row_number": 2,  "column_number": 1,  "sub_level": 1},
    {"character": "キ", "consonant": "k",  "vowel": "i",  "row_number": 2,  "column_number": 2,  "sub_level": 1},
    {"character": "ク", "consonant": "k",  "vowel": "u",  "row_number": 2,  "column_number": 3,  "sub_level": 1},
    {"character": "ケ", "consonant": "k",  "vowel": "e",  "row_number": 2,  "column_number": 4,  "sub_level": 1},
    {"character": "コ", "consonant": "k",  "vowel": "o",  "row_number": 2,  "column_number": 5,  "sub_level": 1},
    {"character": "サ", "consonant": "s",  "vowel": "a",  "row_number": 3,  "column_number": 1,  "sub_level": 1},
    {"character": "シ", "consonant": "sh", "vowel": "i",  "row_number": 3,  "column_number": 2,  "sub_level": 1},
    {"character": "ス", "consonant": "s",  "vowel": "u",  "row_number": 3,  "column_number": 3,  "sub_level": 1},
    {"character": "セ", "consonant": "s",  "vowel": "e",  "row_number": 3,  "column_number": 4,  "sub_level": 1},
    {"character": "ソ", "consonant": "s",  "vowel": "o",  "row_number": 3,  "column_number": 5,  "sub_level": 1},
    {"character": "タ", "consonant": "t",  "vowel": "a",  "row_number": 4,  "column_number": 1,  "sub_level": 1},
    {"character": "チ", "consonant": "ch", "vowel": "i",  "row_number": 4,  "column_number": 2,  "sub_level": 1},
    {"character": "ツ", "consonant": "ts", "vowel": "u",  "row_number": 4,  "column_number": 3,  "sub_level": 1},
    {"character": "テ", "consonant": "t",  "vowel": "e",  "row_number": 4,  "column_number": 4,  "sub_level": 1},
    {"character": "ト", "consonant": "t",  "vowel": "o",  "row_number": 4,  "column_number": 5,  "sub_level": 1},
    {"character": "ナ", "consonant": "n",  "vowel": "a",  "row_number": 5,  "column_number": 1,  "sub_level": 1},
    {"character": "ニ", "consonant": "n",  "vowel": "i",  "row_number": 5,  "column_number": 2,  "sub_level": 1},
    {"character": "ヌ", "consonant": "n",  "vowel": "u",  "row_number": 5,  "column_number": 3,  "sub_level": 1},
    {"character": "ネ", "consonant": "n",  "vowel": "e",  "row_number": 5,  "column_number": 4,  "sub_level": 1},
    {"character": "ノ", "consonant": "n",  "vowel": "o",  "row_number": 5,  "column_number": 5,  "sub_level": 1},
    {"character": "ハ", "consonant": "h",  "vowel": "a",  "row_number": 6,  "column_number": 1,  "sub_level": 1},
    {"character": "ヒ", "consonant": "h",  "vowel": "i",  "row_number": 6,  "column_number": 2,  "sub_level": 1},
    {"character": "フ", "consonant": "f",  "vowel": "u",  "row_number": 6,  "column_number": 3,  "sub_level": 1},
    {"character": "ヘ", "consonant": "h",  "vowel": "e",  "row_number": 6,  "column_number": 4,  "sub_level": 1},
    {"character": "ホ", "consonant": "h",  "vowel": "o",  "row_number": 6,  "column_number": 5,  "sub_level": 1},
    {"character": "マ", "consonant": "m",  "vowel": "a",  "row_number": 7,  "column_number": 1,  "sub_level": 1},
    {"character": "ミ", "consonant": "m",  "vowel": "i",  "row_number": 7,  "column_number": 2,  "sub_level": 1},
    {"character": "ム", "consonant": "m",  "vowel": "u",  "row_number": 7,  "column_number": 3,  "sub_level": 1},
    {"character": "メ", "consonant": "m",  "vowel": "e",  "row_number": 7,  "column_number": 4,  "sub_level": 1},
    {"character": "モ", "consonant": "m",  "vowel": "o",  "row_number": 7,  "column_number": 5,  "sub_level": 1},
    {"character": "ヤ", "consonant": "y",  "vowel": "a",  "row_number": 8,  "column_number": 1,  "sub_level": 1},
    {"character": "ユ", "consonant": "y",  "vowel": "u",  "row_number": 8,  "column_number": 3,  "sub_level": 1},
    {"character": "ヨ", "consonant": "y",  "vowel": "o",  "row_number": 8,  "column_number": 5,  "sub_level": 1},
    {"character": "ラ", "consonant": "r",  "vowel": "a",  "row_number": 9,  "column_number": 1,  "sub_level": 1},
    {"character": "リ", "consonant": "r",  "vowel": "i",  "row_number": 9,  "column_number": 2,  "sub_level": 1},
    {"character": "ル", "consonant": "r",  "vowel": "u",  "row_number": 9,  "column_number": 3,  "sub_level": 1},
    {"character": "レ", "consonant": "r",  "vowel": "e",  "row_number": 9,  "column_number": 4,  "sub_level": 1},
    {"character": "ロ", "consonant": "r",  "vowel": "o",  "row_number": 9,  "column_number": 5,  "sub_level": 1},
    {"character": "ワ", "consonant": "w",  "vowel": "a",  "row_number": 10, "column_number": 1,  "sub_level": 1},
    {"character": "ヲ", "consonant": "w",  "vowel": "o",  "row_number": 10, "column_number": 5,  "sub_level": 1},
    {"character": "ン", "consonant": "n",  "vowel": None, "row_number": 11, "column_number": None, "sub_level": 1},
]

def put_items():
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(TABLE_NAME)

    with table.batch_writer() as batch:
        # ひらがな
        for entry in HIRAGANA_DATA:
            batch.put_item(Item=_build_item(entry, HIRAGANA_LEVEL))
            print(f"Put hiragana: {entry['character']}")

        # カタカナ
        for entry in KATAKANA_DATA:
            batch.put_item(Item=_build_item(entry, KATAKANA_LEVEL))
            print(f"Put katakana: {entry['character']}")

def _build_item(entry: dict, level: int) -> dict:
    char = entry["character"]
    item = {
        "PK": "KANA",
        "SK": char,
        "char": char,
        "level": Decimal(level),
        "consonant": entry["consonant"],
        "vowel": entry["vowel"],
        "row_number": Decimal(entry["row_number"]),
        "sub_level": Decimal(entry["sub_level"]),
    }
    column_number = entry.get("column_number")
    if column_number is not None:
        item["column_number"] = Decimal(column_number)
    return item

if __name__ == "__main__":
    put_items()