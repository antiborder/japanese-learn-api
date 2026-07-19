"""
DynamoDB に Hiragana 2 (level -9) / Katakana 2 (level -6) のマスターデータを登録するスクリプト。

実行方法:
  source venv/bin/activate
  AWS_PROFILE=default python scripts/migrate_kana_advanced.py
"""

import boto3
from decimal import Decimal

TABLE_NAME = "japanese-learn-table"

ADVANCED_DATA = [
    # 濁音
    {"character": "が", "consonant": "g",  "vowel": "a", "row_number": 12, "column_number": 1,  "sub_level": 2},
    {"character": "ぎ", "consonant": "g",  "vowel": "i", "row_number": 12, "column_number": 2,  "sub_level": 2},
    {"character": "ぐ", "consonant": "g",  "vowel": "u", "row_number": 12, "column_number": 3,  "sub_level": 2},
    {"character": "げ", "consonant": "g",  "vowel": "e", "row_number": 12, "column_number": 4,  "sub_level": 2},
    {"character": "ご", "consonant": "g",  "vowel": "o", "row_number": 12, "column_number": 5,  "sub_level": 2},
    {"character": "ざ", "consonant": "z",  "vowel": "a", "row_number": 13, "column_number": 1,  "sub_level": 2},
    {"character": "じ", "consonant": "j",  "vowel": "i", "row_number": 13, "column_number": 2,  "sub_level": 2},
    {"character": "ず", "consonant": "z",  "vowel": "u", "row_number": 13, "column_number": 3,  "sub_level": 2},
    {"character": "ぜ", "consonant": "z",  "vowel": "e", "row_number": 13, "column_number": 4,  "sub_level": 2},
    {"character": "ぞ", "consonant": "z",  "vowel": "o", "row_number": 13, "column_number": 5,  "sub_level": 2},
    {"character": "だ", "consonant": "d",  "vowel": "a", "row_number": 14, "column_number": 1,  "sub_level": 2},
    {"character": "ぢ", "consonant": "d",  "vowel": "i", "row_number": 14, "column_number": 2,  "sub_level": 2},
    {"character": "づ", "consonant": "d",  "vowel": "u", "row_number": 14, "column_number": 3,  "sub_level": 2},
    {"character": "で", "consonant": "d",  "vowel": "e", "row_number": 14, "column_number": 4,  "sub_level": 2},
    {"character": "ど", "consonant": "d",  "vowel": "o", "row_number": 14, "column_number": 5,  "sub_level": 2},
    {"character": "ば", "consonant": "b",  "vowel": "a", "row_number": 15, "column_number": 1,  "sub_level": 2},
    {"character": "び", "consonant": "b",  "vowel": "i", "row_number": 15, "column_number": 2,  "sub_level": 2},
    {"character": "ぶ", "consonant": "b",  "vowel": "u", "row_number": 15, "column_number": 3,  "sub_level": 2},
    {"character": "べ", "consonant": "b",  "vowel": "e", "row_number": 15, "column_number": 4,  "sub_level": 2},
    {"character": "ぼ", "consonant": "b",  "vowel": "o", "row_number": 15, "column_number": 5,  "sub_level": 2},
    # 半濁音
    {"character": "ぱ", "consonant": "p",  "vowel": "a", "row_number": 16, "column_number": 1,  "sub_level": 2},
    {"character": "ぴ", "consonant": "p",  "vowel": "i", "row_number": 16, "column_number": 2,  "sub_level": 2},
    {"character": "ぷ", "consonant": "p",  "vowel": "u", "row_number": 16, "column_number": 3,  "sub_level": 2},
    {"character": "ぺ", "consonant": "p",  "vowel": "e", "row_number": 16, "column_number": 4,  "sub_level": 2},
    {"character": "ぽ", "consonant": "p",  "vowel": "o", "row_number": 16, "column_number": 5,  "sub_level": 2},
    # 拗音
    {"character": "きゃ", "consonant": "ky", "vowel": "a", "row_number": 17, "column_number": 1, "sub_level": 2},
    {"character": "きゅ", "consonant": "ky", "vowel": "u", "row_number": 17, "column_number": 3, "sub_level": 2},
    {"character": "きょ", "consonant": "ky", "vowel": "o", "row_number": 17, "column_number": 5, "sub_level": 2},
    {"character": "しゃ", "consonant": "sh", "vowel": "a", "row_number": 18, "column_number": 1, "sub_level": 2},
    {"character": "しゅ", "consonant": "sh", "vowel": "u", "row_number": 18, "column_number": 3, "sub_level": 2},
    {"character": "しょ", "consonant": "sh", "vowel": "o", "row_number": 18, "column_number": 5, "sub_level": 2},
    {"character": "ちゃ", "consonant": "ch", "vowel": "a", "row_number": 19, "column_number": 1, "sub_level": 2},
    {"character": "ちゅ", "consonant": "ch", "vowel": "u", "row_number": 19, "column_number": 3, "sub_level": 2},
    {"character": "ちょ", "consonant": "ch", "vowel": "o", "row_number": 19, "column_number": 5, "sub_level": 2},
    {"character": "にゃ", "consonant": "ny", "vowel": "a", "row_number": 20, "column_number": 1, "sub_level": 2},
    {"character": "にゅ", "consonant": "ny", "vowel": "u", "row_number": 20, "column_number": 3, "sub_level": 2},
    {"character": "にょ", "consonant": "ny", "vowel": "o", "row_number": 20, "column_number": 5, "sub_level": 2},
    {"character": "ひゃ", "consonant": "hy", "vowel": "a", "row_number": 21, "column_number": 1, "sub_level": 2},
    {"character": "ひゅ", "consonant": "hy", "vowel": "u", "row_number": 21, "column_number": 3, "sub_level": 2},
    {"character": "ひょ", "consonant": "hy", "vowel": "o", "row_number": 21, "column_number": 5, "sub_level": 2},
    {"character": "みゃ", "consonant": "my", "vowel": "a", "row_number": 22, "column_number": 1, "sub_level": 2},
    {"character": "みゅ", "consonant": "my", "vowel": "u", "row_number": 22, "column_number": 3, "sub_level": 2},
    {"character": "みょ", "consonant": "my", "vowel": "o", "row_number": 22, "column_number": 5, "sub_level": 2},
    {"character": "りゃ", "consonant": "ry", "vowel": "a", "row_number": 23, "column_number": 1, "sub_level": 2},
    {"character": "りゅ", "consonant": "ry", "vowel": "u", "row_number": 23, "column_number": 3, "sub_level": 2},
    {"character": "りょ", "consonant": "ry", "vowel": "o", "row_number": 23, "column_number": 5, "sub_level": 2},
    # 濁音拗音
    {"character": "ぎゃ", "consonant": "gy", "vowel": "a", "row_number": 24, "column_number": 1, "sub_level": 2},
    {"character": "ぎゅ", "consonant": "gy", "vowel": "u", "row_number": 24, "column_number": 3, "sub_level": 2},
    {"character": "ぎょ", "consonant": "gy", "vowel": "o", "row_number": 24, "column_number": 5, "sub_level": 2},
    {"character": "じゃ", "consonant": "j",  "vowel": "a", "row_number": 25, "column_number": 1, "sub_level": 2},
    {"character": "じゅ", "consonant": "j",  "vowel": "u", "row_number": 25, "column_number": 3, "sub_level": 2},
    {"character": "じょ", "consonant": "j",  "vowel": "o", "row_number": 25, "column_number": 5, "sub_level": 2},
    {"character": "びゃ", "consonant": "by", "vowel": "a", "row_number": 26, "column_number": 1, "sub_level": 2},
    {"character": "びゅ", "consonant": "by", "vowel": "u", "row_number": 26, "column_number": 3, "sub_level": 2},
    {"character": "びょ", "consonant": "by", "vowel": "o", "row_number": 26, "column_number": 5, "sub_level": 2},
    {"character": "ぴゃ", "consonant": "py", "vowel": "a", "row_number": 27, "column_number": 1, "sub_level": 2},
    {"character": "ぴゅ", "consonant": "py", "vowel": "u", "row_number": 27, "column_number": 3, "sub_level": 2},
    {"character": "ぴょ", "consonant": "py", "vowel": "o", "row_number": 27, "column_number": 5, "sub_level": 2},
]

HIRAGANA_TO_KATAKANA_OFFSET = 0x60


def to_katakana(char: str) -> str:
    return "".join(chr(ord(c) + HIRAGANA_TO_KATAKANA_OFFSET) for c in char)


def build_romaji(consonant, vowel):
    if not consonant and not vowel:
        return "n"
    if not consonant:
        return vowel or ""
    if not vowel:
        return consonant
    return consonant + vowel


def main():
    dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")
    table = dynamodb.Table(TABLE_NAME)

    hiragana_items = []
    katakana_items = []

    for d in ADVANCED_DATA:
        romaji = build_romaji(d["consonant"], d["vowel"])
        kata_char = to_katakana(d["character"])

        hiragana_items.append({
            "PK": "KANA",
            "SK": f"HIRAGANA#{d['character']}",
            "char": d["character"],
            "character": d["character"],
            "consonant": d["consonant"],
            "vowel": d["vowel"],
            "romaji": romaji,
            "row_number": Decimal(str(d["row_number"])),
            "column_number": Decimal(str(d["column_number"])) if d["column_number"] is not None else None,
            "sub_level": Decimal(str(d["sub_level"])),
            "level": Decimal("-9"),
        })

        katakana_items.append({
            "PK": "KANA",
            "SK": f"KATAKANA#{kata_char}",
            "char": kata_char,
            "character": kata_char,
            "hiragana_character": d["character"],
            "consonant": d["consonant"],
            "vowel": d["vowel"],
            "romaji": romaji,
            "row_number": Decimal(str(d["row_number"])),
            "column_number": Decimal(str(d["column_number"])) if d["column_number"] is not None else None,
            "sub_level": Decimal(str(d["sub_level"])),
            "level": Decimal("-6"),
        })

    all_items = hiragana_items + katakana_items
    print(f"Inserting {len(hiragana_items)} hiragana items (level -9) and {len(katakana_items)} katakana items (level -6)...")

    with table.batch_writer() as batch:
        for item in all_items:
            item_clean = {k: v for k, v in item.items() if v is not None}
            batch.put_item(Item=item_clean)

    print("Done.")


if __name__ == "__main__":
    main()
