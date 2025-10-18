#!/usr/bin/env python3
"""
ユーザー設定のマイグレーションスクリプト
既存のユーザーにデフォルトの設定を追加します
"""

import boto3
import json
import logging
import os
from datetime import datetime, timezone
from botocore.exceptions import ClientError

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DynamoDBクライアントの初期化
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
table = dynamodb.Table(table_name)

# デフォルト設定
DEFAULT_SETTINGS = {
    'base_level': 1,
    'theme': 'Summer',
    'language': 'en'
}

def get_all_users():
    """
    既存のユーザーIDを取得する
    """
    try:
        # ユーザーの学習履歴からユーザーIDを抽出
        response = table.scan(
            FilterExpression='begins_with(PK, :pk_prefix)',
            ExpressionAttributeValues={
                ':pk_prefix': 'USER#'
            },
            ProjectionExpression='PK'
        )
        
        user_ids = set()
        for item in response['Items']:
            pk = item['PK']
            if pk.startswith('USER#'):
                user_id = pk.replace('USER#', '')
                user_ids.add(user_id)
        
        return list(user_ids)
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise

def check_user_settings_exist(user_id):
    """
    ユーザーの設定が既に存在するかチェックする
    """
    try:
        response = table.get_item(
            Key={
                'PK': f"USER#{user_id}",
                'SK': 'SETTINGS'
            }
        )
        return 'Item' in response
    except Exception as e:
        logger.error(f"Error checking user settings for {user_id}: {str(e)}")
        return False

def create_default_settings(user_id):
    """
    ユーザーにデフォルト設定を作成する
    """
    try:
        now = datetime.now(timezone.utc).isoformat()
        
        item = {
            'PK': f"USER#{user_id}",
            'SK': 'SETTINGS',
            'base_level': DEFAULT_SETTINGS['base_level'],
            'theme': DEFAULT_SETTINGS['theme'],
            'language': DEFAULT_SETTINGS['language'],
            'created_at': now,
            'updated_at': now
        }
        
        table.put_item(Item=item)
        logger.info(f"Created default settings for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error creating settings for user {user_id}: {str(e)}")
        return False

def check_table_exists():
    """
    テーブルが存在するかチェックする
    """
    try:
        table.load()
        logger.info(f"Table {table_name} exists and is accessible")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.error(f"Table {table_name} does not exist")
            return False
        else:
            logger.error(f"Error checking table: {str(e)}")
            raise

def migrate_user_settings():
    """
    ユーザー設定のマイグレーションを実行する
    """
    try:
        logger.info("Starting user settings migration...")
        logger.info(f"Using table: {table_name}")
        
        # テーブルの存在確認
        if not check_table_exists():
            logger.error("Table does not exist. Please check your AWS configuration and table name.")
            return
        
        # 全てのユーザーを取得
        user_ids = get_all_users()
        logger.info(f"Found {len(user_ids)} users")
        
        if not user_ids:
            logger.info("No users found. Migration completed.")
            return
        
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        for user_id in user_ids:
            try:
                # 既存の設定をチェック
                if check_user_settings_exist(user_id):
                    logger.info(f"Settings already exist for user {user_id}, skipping...")
                    skipped_count += 1
                    continue
                
                # デフォルト設定を作成
                if create_default_settings(user_id):
                    migrated_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing user {user_id}: {str(e)}")
                error_count += 1
        
        logger.info(f"Migration completed:")
        logger.info(f"  - Migrated: {migrated_count}")
        logger.info(f"  - Skipped: {skipped_count}")
        logger.info(f"  - Errors: {error_count}")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

def print_usage():
    """
    使用方法を表示する
    """
    print("""
使用方法:
1. 環境変数を設定して実行:
   export DYNAMODB_TABLE_NAME=your-table-name
   python scripts/migrate_user_settings.py

2. または、直接テーブル名を指定:
   DYNAMODB_TABLE_NAME=your-table-name python scripts/migrate_user_settings.py

3. AWS認証情報が設定されていることを確認してください:
   aws configure list
   """)

if __name__ == "__main__":
    # テーブル名が設定されているかチェック
    if not os.getenv('DYNAMODB_TABLE_NAME'):
        print("警告: DYNAMODB_TABLE_NAME環境変数が設定されていません。")
        print("デフォルトのテーブル名 'japanese-learn-table' を使用します。")
        print_usage()
    
    migrate_user_settings()
