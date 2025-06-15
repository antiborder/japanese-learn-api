import json
import logging
import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException
from typing import List, Optional

# ロギングの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="Japanese Learn API - Kanjis and Components",
    description="API for managing Japanese kanjis and their components",
    version="1.0.0"
)


# エンドポイントのインポート
from endpoints.kanji import router as kanji_router
from endpoints.component import router as component_router

app.include_router(kanji_router, prefix="/api/v1/kanjis", tags=["kanjis"])
app.include_router(component_router, prefix="/api/v1/components", tags=["components"])

# Mangumハンドラーの作成
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    try:
        # Mangumハンドラーを使用してFastAPIアプリケーションをLambdaで実行
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