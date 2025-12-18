import json
import logging
import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException

# ロギングの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数からroot_pathを取得（ローカル開発時は空文字）
ROOT_PATH = os.getenv('ROOT_PATH', '')

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="Japanese Learn API - Chat",
    description="AI Chatbot API for Japanese language learning",
    version="1.0.0",
    root_path=ROOT_PATH
)

# エンドポイントのインポート
from endpoints.chat import router as chat_router
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])

# Mangumハンドラーの作成
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    try:
        # OPTIONSリクエストをLambda関数内で先に処理（Mangum/FastAPIに渡す前に）
        # API GatewayのANYメソッドがOPTIONSもキャッチするため、ここで処理する必要がある
        http_method = event.get('httpMethod') or event.get('requestContext', {}).get('httpMethod', '')
        
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Origin,Accept',
                    'Access-Control-Max-Age': '86400',
                    'Content-Type': 'application/json'
                },
                'body': ''
            }
        
        # Mangumハンドラーを使用してFastAPIアプリケーションをLambdaで実行
        stage = event.get('requestContext', {}).get('stage', '')
        if stage:
            app.root_path = f"/{stage}"
        response = handler(event, context)
        
        # レスポンスにCORSヘッダーを追加
        if 'headers' not in response:
            response['headers'] = {}
        
        response['headers'].update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PUT,DELETE',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Origin,Accept'
        })
        
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
                'Access-Control-Allow-Origin': '*'
            }
        }

