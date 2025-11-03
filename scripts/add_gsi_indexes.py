#!/usr/bin/env python3
"""
DynamoDBテーブルにGlobal Secondary Index (GSI)を追加するスクリプト

CloudFormationでは一度に複数のGSIを追加できないため、
このスクリプトでAWS CLIを使用して1つずつ追加します。
"""

import boto3
import os
import sys
import time
from botocore.exceptions import ClientError

# AWS認証情報を設定（環境変数または~/.aws/credentialsから自動取得）
# AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION を使用

class GSIAdder:
    def __init__(self, table_name: str, region_name: str = 'us-east-1'):
        """
        GSIAdderの初期化
        
        Args:
            table_name: DynamoDBテーブル名
            region_name: AWSリージョン名
        """
        self.table_name = table_name
        self.region_name = region_name
        self.dynamodb = boto3.client('dynamodb', region_name=region_name)
        
    def check_existing_indexes(self):
        """既存のGSIを確認"""
        try:
            response = self.dynamodb.describe_table(TableName=self.table_name)
            table = response['Table']
            existing_indexes = [gsi['IndexName'] for gsi in table.get('GlobalSecondaryIndexes', [])]
            print(f"既存のGSIインデックス: {existing_indexes}")
            return existing_indexes
        except ClientError as e:
            print(f"エラー: テーブルの情報取得に失敗しました: {e}")
            raise
    
    def add_index(self, index_name: str, attribute_name: str):
        """
        新しいGSIを追加
        
        Args:
            index_name: インデックス名
            attribute_name: パーティションキーの属性名
        """
        try:
            print(f"\nインデックス '{index_name}' を追加中...")
            
            # GSIの定義
            gsi_update = {
                'Create': {
                    'IndexName': index_name,
                    'KeySchema': [
                        {
                            'AttributeName': attribute_name,
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            }
            
            # インデックスの追加を開始
            response = self.dynamodb.update_table(
                TableName=self.table_name,
                AttributeDefinitions=[
                    {
                        'AttributeName': attribute_name,
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexUpdates=[gsi_update]
            )
            
            print(f"✓ インデックス '{index_name}' の追加を開始しました")
            
            # インデックスの作成完了を待機
            index_status = 'CREATING'
            while index_status == 'CREATING':
                time.sleep(5)
                response = self.dynamodb.describe_table(TableName=self.table_name)
                table = response['Table']
                
                # 該当インデックスのステータスを確認
                for gsi in table.get('GlobalSecondaryIndexes', []):
                    if gsi['IndexName'] == index_name:
                        index_status = gsi['IndexStatus']
                        print(f"  ステータス: {index_status}")
                        break
            
            if index_status == 'ACTIVE':
                print(f"✓ インデックス '{index_name}' が正常に作成されました")
                return True
            else:
                print(f"✗ インデックス '{index_name}' の作成に失敗しました (ステータス: {index_status})")
                return False
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceInUseException':
                print(f"! インデックス '{index_name}' は既に存在します")
                return True
            else:
                print(f"✗ エラー: インデックス '{index_name}' の追加に失敗しました: {e}")
                return False

def main():
    """メイン処理"""
    # 環境変数からテーブル名を取得
    table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
    region_name = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    
    print("=" * 60)
    print("DynamoDB GSI インデックス追加スクリプト")
    print("=" * 60)
    print(f"テーブル名: {table_name}")
    print(f"リージョン: {region_name}")
    
    # 追加するGSIインデックスの定義
    gsis_to_add = [
        ('chinese-index', 'chinese'),
        ('korean-index', 'korean'),
        ('indonesian-index', 'indonesian'),
        ('hindi-index', 'hindi'),
    ]
    
    try:
        # GSIAdderを初期化
        adder = GSIAdder(table_name, region_name)
        
        # 既存のインデックスを確認
        print("\n既存のインデックスを確認中...")
        existing_indexes = adder.check_existing_indexes()
        
        # まだ存在しないインデックスのみ追加
        indexes_to_create = []
        for index_name, attr_name in gsis_to_add:
            if index_name not in existing_indexes:
                indexes_to_create.append((index_name, attr_name))
        
        if not indexes_to_create:
            print("\n✓ すべてのインデックスが既に存在しています")
            return
        
        print(f"\n追加するインデックス: {len(indexes_to_create)}個")
        for index_name, _ in indexes_to_create:
            print(f"  - {index_name}")
        
        # 確認
        confirm = input("\nこれらのインデックスを追加しますか？ (y/n): ")
        if confirm.lower() != 'y':
            print("キャンセルしました")
            return
        
        # インデックスを1つずつ追加
        success_count = 0
        for index_name, attr_name in indexes_to_create:
            if adder.add_index(index_name, attr_name):
                success_count += 1
        
        # 結果表示
        print("\n" + "=" * 60)
        print("インデックス追加完了")
        print("=" * 60)
        print(f"成功: {success_count}/{len(indexes_to_create)}個のインデックス")
        
        if success_count < len(indexes_to_create):
            print("\n一部のインデックスの追加に失敗しました")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n✗ エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

