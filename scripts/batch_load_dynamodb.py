import boto3
import csv
import os
from typing import List, Dict
from datetime import datetime

class DynamoDBDataLoader:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def load_csv_file(self, file_path: str) -> List[Dict]:
        """CSVファイルを読み込んでデータのリストを返す"""
        items = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # 最初の2列がPKとSKであることを前提とする
            reader = csv.reader(f)
            headers = next(reader)
            
            if len(headers) < 2:
                raise ValueError("CSVファイルには最低2列（PK, SK）が必要です")
            
            for row in reader:
                if len(row) < 2:
                    continue  # PKとSKが無い行はスキップ
                
                item = {
                    'PK': row[0],
                    'SK': row[1] if row[1] else f"METADATA#{row[0].split('#')[0]}",
                    'createdAt': datetime.now().isoformat(),
                    'updatedAt': datetime.now().isoformat()
                }
                
                # 残りの列を属性として追加
                for i, value in enumerate(row[2:], 2):
                    if value.strip():  # 空値は保存しない
                        attr_name = headers[i]
                        item[attr_name] = self._convert_value(value)
                
                items.append(item)
        
        return items

    def _convert_value(self, value: str):
        """値の型を適切に変換"""
        value = value.strip()
        
        # 整数への変換を試みる
        try:
            if value.isdigit():
                return int(value)
        except ValueError:
            pass

        # 浮動小数点数への変換を試みる
        try:
            return float(value)
        except ValueError:
            pass

        # セミコロン区切りの文字列はリストとして扱う
        if ';' in value:
            return [v.strip() for v in value.split(';') if v.strip()]

        return value

    def batch_write_items(self, items: List[Dict]) -> None:
        """DynamoDBにバッチ書き込みを行う"""
        chunk_size = 25
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
    loader = DynamoDBDataLoader(table_name)
    
    # dataディレクトリ内のすべてのCSVファイルを処理
    data_dir = 'data'
    for file_name in os.listdir(data_dir):
        if file_name.endswith('.csv'):
            csv_path = os.path.join(data_dir, file_name)
            data_type = os.path.splitext(file_name)[0].upper()
            print(f"\nProcessing {data_type} from {csv_path}")
            
            try:
                items = loader.load_csv_file(csv_path)
                print(f"Found {len(items)} {data_type} items in CSV file.")
                
                if items:
                    print(f"Starting batch write to {table_name}...")
                    loader.batch_write_items(items)
                    print(f"Batch write completed for {data_type}.")
            except Exception as e:
                print(f"Error processing {csv_path}: {str(e)}")

if __name__ == "__main__":
    main() 