import json
import logging
import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException
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
    title="Japanese Learn API - Sentences",
    description="API for managing Japanese sentences",
    version="1.0.0",
    root_path=ROOT_PATH
)

# エンドポイントのインポート
from endpoints.sentence import router
app.include_router(router, prefix="/api/v1/sentences", tags=["sentences"])

# Mangumハンドラーの作成
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    try:
        # リクエスト情報をログに記録
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Mangumハンドラーでリクエストを処理
        response = handler(event, context)
        
        # レスポンス情報をログに記録
        logger.info(f"Response: {json.dumps(response)}")
        
        return response
        
    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'
            },
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': str(e)
            })
        }
