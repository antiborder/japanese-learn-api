#!/usr/bin/env python3
"""
DynamoDBのレコードを削除するスクリプト

削除対象:
1. PK=KANJI
2. PK=COMPONENT
3. PK=KANJI#で始まる and SK=WORD#で始まる
4. PK=WORD#で始まる and SK=KANJI#
5. PK=KANJI#で始まる and SK=COMPONENT#で始まる
6. PK=COMPONENT#で始まる and SK=KANJI#
"""

import boto3
import os
from typing import List, Dict, Any
from botocore.exceptions import ClientError

class DynamoDBDeleter:
    def __init__(self, table_name: str, region_name: str = 'us-east-1'):
        """
        DynamoDBDeleterの初期化
        
        Args:
            table_name: DynamoDBテーブル名
            region_name: AWSリージョン名（使用されません、import_dynamodb.pyとの互換性のため）
        """
        self.table_name = table_name
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        
    def delete_records_by_pk(self, pk_value: str) -> int:
        """
        PKが指定された値と一致するレコードを削除
        
        Args:
            pk_value: 削除対象のPK値
            
        Returns:
            削除されたレコード数
        """
        deleted_count = 0
        
        try:
            # QueryでPKが一致するレコードを取得
            response = self.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': pk_value
                }
            )
            
            items = response.get('Items', [])
            
            # 取得したレコードを削除
            for item in items:
                try:
                    self.table.delete_item(
                        Key={
                            'PK': item['PK'],
                            'SK': item['SK']
                        }
                    )
                    deleted_count += 1
                    print(f"削除: PK={item['PK']}, SK={item['SK']}")
                except ClientError as e:
                    print(f"削除エラー: PK={item['PK']}, SK={item['SK']}, エラー={e}")
            
            # ページネーション処理
            while 'LastEvaluatedKey' in response:
                response = self.table.query(
                    KeyConditionExpression='PK = :pk',
                    ExpressionAttributeValues={
                        ':pk': pk_value
                    },
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                
                items = response.get('Items', [])
                for item in items:
                    try:
                        self.table.delete_item(
                            Key={
                                'PK': item['PK'],
                                'SK': item['SK']
                            }
                        )
                        deleted_count += 1
                        print(f"削除: PK={item['PK']}, SK={item['SK']}")
                    except ClientError as e:
                        print(f"削除エラー: PK={item['PK']}, SK={item['SK']}, エラー={e}")
                        
        except ClientError as e:
            print(f"クエリエラー: PK={pk_value}, エラー={e}")
            
        return deleted_count
    
    def delete_records_by_pk_sk_prefix(self, pk_prefix: str, sk_prefix: str) -> int:
        """
        PKが指定されたプレフィックスで始まり、SKも指定されたプレフィックスで始まるレコードを削除
        
        Args:
            pk_prefix: PKのプレフィックス
            sk_prefix: SKのプレフィックス
            
        Returns:
            削除されたレコード数
        """
        deleted_count = 0
        
        try:
            # Scanで全レコードを取得し、条件に合うものを削除
            response = self.table.scan()
            items = response.get('Items', [])
            
            for item in items:
                pk = item.get('PK', '')
                sk = item.get('SK', '')
                
                if pk.startswith(pk_prefix) and sk.startswith(sk_prefix):
                    try:
                        self.table.delete_item(
                            Key={
                                'PK': pk,
                                'SK': sk
                            }
                        )
                        deleted_count += 1
                        print(f"削除: PK={pk}, SK={sk}")
                    except ClientError as e:
                        print(f"削除エラー: PK={pk}, SK={sk}, エラー={e}")
            
            # ページネーション処理
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                
                items = response.get('Items', [])
                for item in items:
                    pk = item.get('PK', '')
                    sk = item.get('SK', '')
                    
                    if pk.startswith(pk_prefix) and sk.startswith(sk_prefix):
                        try:
                            self.table.delete_item(
                                Key={
                                    'PK': pk,
                                    'SK': sk
                                }
                            )
                            deleted_count += 1
                            print(f"削除: PK={pk}, SK={sk}")
                        except ClientError as e:
                            print(f"削除エラー: PK={pk}, SK={sk}, エラー={e}")
                            
        except ClientError as e:
            print(f"スキャンエラー: エラー={e}")
            
        return deleted_count
    
    def delete_all_target_records(self) -> Dict[str, int]:
        """
        指定された条件の全てのレコードを削除
        
        Returns:
            各条件で削除されたレコード数の辞書
        """
        results = {}
        
        print("DynamoDBレコード削除開始")
        print("=" * 50)
        
        # 1. PK=KANJI
        print("\n1. PK=KANJI のレコードを削除中...")
        count = self.delete_records_by_pk('KANJI')
        results['PK=KANJI'] = count
        print(f"削除完了: {count}件")
        
        # 2. PK=COMPONENT
        print("\n2. PK=COMPONENT のレコードを削除中...")
        count = self.delete_records_by_pk('COMPONENT')
        results['PK=COMPONENT'] = count
        print(f"削除完了: {count}件")
        
        # 3. PK=KANJI#で始まる and SK=WORD#で始まる
        print("\n3. PK=KANJI#で始まる and SK=WORD#で始まるレコードを削除中...")
        count = self.delete_records_by_pk_sk_prefix('KANJI#', 'WORD#')
        results['PK=KANJI# and SK=WORD#'] = count
        print(f"削除完了: {count}件")
        
        # 4. PK=WORD#で始まる and SK=KANJI#
        print("\n4. PK=WORD#で始まる and SK=KANJI#のレコードを削除中...")
        count = self.delete_records_by_pk_sk_prefix('WORD#', 'KANJI#')
        results['PK=WORD# and SK=KANJI#'] = count
        print(f"削除完了: {count}件")
        
        # 5. PK=KANJI#で始まる and SK=COMPONENT#で始まる
        print("\n5. PK=KANJI#で始まる and SK=COMPONENT#で始まるレコードを削除中...")
        count = self.delete_records_by_pk_sk_prefix('KANJI#', 'COMPONENT#')
        results['PK=KANJI# and SK=COMPONENT#'] = count
        print(f"削除完了: {count}件")
        
        # 6. PK=COMPONENT#で始まる and SK=KANJI#
        print("\n6. PK=COMPONENT#で始まる and SK=KANJI#のレコードを削除中...")
        count = self.delete_records_by_pk_sk_prefix('COMPONENT#', 'KANJI#')
        results['PK=COMPONENT# and SK=KANJI#'] = count
        print(f"削除完了: {count}件")
        
        return results

def main():
    """メイン処理"""
    # 環境変数からテーブル名を取得（import_dynamodb.pyと同じ方法）
    table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
    region_name = os.environ.get('AWS_REGION', 'us-east-1')
    
    print(f"テーブル名: {table_name}")
    print(f"リージョン: {region_name}")
    
    # 確認メッセージ
    print("\n⚠️  警告: このスクリプトは指定された条件のレコードを完全に削除します")
    print("削除対象:")
    print("1. PK=KANJI")
    print("2. PK=COMPONENT")
    print("3. PK=KANJI#で始まる and SK=WORD#で始まる")
    print("4. PK=WORD#で始まる and SK=KANJI#")
    print("5. PK=KANJI#で始まる and SK=COMPONENT#で始まる")
    print("6. PK=COMPONENT#で始まる and SK=KANJI#")
    
    confirm = input("\n本当に削除しますか？ (yes/no): ")
    if confirm.lower() != 'yes':
        print("削除をキャンセルしました")
        return
    
    try:
        # DynamoDBDeleterを初期化
        deleter = DynamoDBDeleter(table_name, region_name)
        
        # 削除実行
        results = deleter.delete_all_target_records()
        
        # 結果表示
        print("\n" + "=" * 50)
        print("削除完了!")
        print("削除結果:")
        total_deleted = 0
        for condition, count in results.items():
            print(f"  {condition}: {count}件")
            total_deleted += count
        
        print(f"\n合計削除件数: {total_deleted}件")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main() 