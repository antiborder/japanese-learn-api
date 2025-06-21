import json
import logging
import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException
from typing import List, Optional

# ロギングの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数からroot_pathを取得（ローカル開発時は空文字）
ROOT_PATH = os.getenv('ROOT_PATH', '')

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="Japanese Learn API - Authentication",
    description="API for user authentication",
    version="1.0.0",
    root_path=ROOT_PATH
)

# 現在、認証エンドポイントは使用されていない
# フロントエンドが直接Cognitoを使用しているため

# Mangumハンドラーの作成
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    try:
        # Mangumハンドラーを使用してFastAPIアプリケーションをLambdaで実行
        stage = event.get('requestContext', {}).get('stage', '')
        if stage:
            app.root_path = f"/{stage}"
        response = handler(event, context)
        
        # レスポンスにCORSヘッダーを追加
        if 'headers' not in response:
            response['headers'] = {}
        
        response['headers'].update({
            'Access-Control-Allow-Origin': '*',  # same-originなので'*'で問題なし
            'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PUT,DELETE',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
        })
        
        # OPTIONSリクエストの場合は、ここで処理を終了
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': response['headers'],
                'body': ''
            }
        
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',  # same-originなので'*'で問題なし
                'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PUT,DELETE',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            }
        } 