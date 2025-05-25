import json
import logging
import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError
from fastapi.middleware.cors import CORSMiddleware

# ロギングの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="Japanese Learn API - Words",
    description="API for managing Japanese words",
    version="1.0.0",
    root_path="/Prod"
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # ローカル開発環境
        "http://bucket-japanese-learn.s3-website-ap-northeast-1.amazonaws.com"  # S3スタティックウェブサイト
    ],
    allow_credentials=True,
    allow_methods=["*"],  # すべてのHTTPメソッドを許可
    allow_headers=["*"],  # すべてのヘッダーを許可
)

# エンドポイントのインポート
from endpoints.word import router
app.include_router(router, prefix="/api/v1/words", tags=["words"])

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