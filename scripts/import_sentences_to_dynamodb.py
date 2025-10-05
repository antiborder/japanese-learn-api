import boto3
import csv
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

class SentencesDataLoader:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def parse_csv_row(self, row):
        """CSVの行を解析してDynamoDB用のデータ形式に変換する"""
        sentence_id = int(row["No."])
        japanese = row["japanese"]
        level = int(row["level"])
        english = row["english"]
        vietnamese = row["vietnamese"]
        grammar_raw = row["grammar"]
        
        # grammar列は "65" や "3,3" のように複数の場合がある
        grammar_ids = [int(g) for g in grammar_raw.replace('"', '').split(",") if g.isdigit()]

        # word_name, word_id のペアを最大14個ほど処理
        words = []
        for i in range(1, 15):
            name_key = f"word{i}_name"
            id_key = f"word{i}_id"
            if row.get(name_key):
                word_name = row[name_key]
                word_id = int(row[id_key]) if row.get(id_key) and row[id_key].isdigit() else None
                words.append({"word_name": word_name, "word_id": word_id})
        
        # ダミー単語は grammar列以降の「候補語」から選ぶ
        dummy_candidates = []
        for i in range(7, 17):  # grammarの右の列
            cell = row.get(str(i))
            if cell and cell != "#N/A":
                dummy_candidates.append(cell)

        return {
            "sentence_id": sentence_id,
            "japanese": japanese,
            "level": level,
            "english": english,
            "vietnamese": vietnamese,
            "grammar_ids": grammar_ids,
            "words": words,
            "dummy_words": dummy_candidates
        }

    def load_sentences_csv(self, file_path: str) -> List[Dict]:
        """sentences CSVファイルを読み込んでデータのリストを返す"""
        items = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            
            for row in csv_reader:
                try:
                    # CSVの行を解析
                    sentence_data = self.parse_csv_row(row)
                    
                    # DynamoDB用のアイテムを作成
                    item = {
                        "PK": "SENTENCE",
                        "SK": str(sentence_data["sentence_id"]),
                        "sentence_id": sentence_data["sentence_id"],
                        "japanese": sentence_data["japanese"],
                        "level": sentence_data["level"],
                        "english": sentence_data["english"],
                        "vietnamese": sentence_data["vietnamese"],
                        "grammar_ids": sentence_data["grammar_ids"],
                        "words": sentence_data["words"],
                        "dummy_words": sentence_data["dummy_words"],
                        "createdAt": datetime.now(timezone.utc).isoformat(),
                        "updatedAt": datetime.now(timezone.utc).isoformat()
                    }
                    
                    items.append(item)
                    print(f"文{sentence_data['sentence_id']}を解析しました: {sentence_data['japanese']}")
                    
                except Exception as e:
                    print(f"エラー: 行の処理中にエラーが発生しました: {e}")
                    print(f"問題のある行: {row}")
                    continue
        
        return items

    def batch_write_items(self, items: List[Dict]) -> None:
        """DynamoDBにバッチ書き込みを行う"""
        chunk_size = 25  # DynamoDBのバッチ書き込み制限に合わせる
        chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            try:
                with self.table.batch_writer() as batch:
                    for item in chunk:
                        batch.put_item(Item=item)
                print(f"Batch {i+1}/{len(chunks)} completed. {len(chunk)} items written.")
            except Exception as e:
                print(f"Error in batch {i+1}: {str(e)}")

def main():
    # 環境変数からテーブル名を取得
    table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
    
    # ローダーの初期化
    loader = SentencesDataLoader(table_name)
    
    # sentences CSVファイルを処理
    csv_path = 'data/dynamodb_source/sentences_20251005.csv'
    
    if not os.path.exists(csv_path):
        print(f"CSVファイルが見つかりません: {csv_path}")
        return
    
    print(f"Processing sentences from {csv_path}")
    
    try:
        items = loader.load_sentences_csv(csv_path)
        print(f"Found {len(items)} sentence items in CSV file.")
        
        if items:
            print(f"Starting batch write to {table_name}...")
            loader.batch_write_items(items)
            print(f"Batch write completed for sentences.")
    except Exception as e:
        print(f"Error processing {csv_path}: {str(e)}")

if __name__ == "__main__":
    main()