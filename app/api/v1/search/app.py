import json
import logging
import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError

# ロギングの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数からroot_pathを取得（ローカル開発時は空文字）
ROOT_PATH = os.getenv('ROOT_PATH', '')

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="Japanese Learn API - Search",
    description="統合検索API（単語、漢字、例文検索）",
    version="1.0.0",
    root_path=ROOT_PATH
)

# CORSミドルウェアを追加（ローカル開発時のみ）
# Lambda環境では、lambda_handler内でCORSヘッダーを設定するため、ミドルウェアは無効化
if not os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# エンドポイントのインポート
from endpoints.search import router
app.include_router(router, prefix="/api/v1/search", tags=["search"])

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
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PUT,DELETE',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
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
