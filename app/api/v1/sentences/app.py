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

# 許可されたオリジンのリスト
ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'https://nihongo.cloud'
]

def get_allowed_origin(event):
    """リクエストのOriginヘッダーを確認し、許可されたオリジンの場合のみ返す"""
    # リクエストヘッダーからOriginを取得
    headers = event.get('headers', {}) or {}
    # API Gatewayはヘッダー名を小文字に変換する場合があるため、両方を確認
    origin = headers.get('Origin') or headers.get('origin')
    
    if origin and origin in ALLOWED_ORIGINS:
        return origin
    
    # Originが無い、または許可されていない場合はNoneを返す
    return None

def lambda_handler(event, context):
    try:
        # リクエスト情報をログに記録
        logger.info(f"Received event: {json.dumps(event)}")
        
        # OPTIONSリクエスト（プリフライトリクエスト）の処理
        http_method = event.get('httpMethod') or event.get('requestContext', {}).get('httpMethod', '')
        if http_method == 'OPTIONS':
            allowed_origin = get_allowed_origin(event)
            logger.info(f"OPTIONS request received. Origin: {event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')}, Allowed: {allowed_origin}")
            
            if allowed_origin:
                # 許可されたOriginの場合のみCORSヘッダーを返す
                cors_headers = {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': allowed_origin,
                    'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PUT,DELETE',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Origin,Accept',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Max-Age': '86400'
                }
                logger.info(f"Returning CORS headers with allowed origin: {allowed_origin}")
                return {
                    'statusCode': 200,
                    'headers': cors_headers,
                    'body': ''
                }
            else:
                # 許可されていないOriginの場合は、CORSヘッダーを一切返さない
                logger.warning(f"Origin not allowed. No CORS headers will be returned.")
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': ''
                }
        
        # Mangumハンドラーでリクエストを処理
        response = handler(event, context)
        
        # レスポンスにCORSヘッダーを追加（許可されたオリジンのみ）
        if 'headers' not in response:
            response['headers'] = {}
        
        allowed_origin = get_allowed_origin(event)
        if allowed_origin:
            response['headers'].update({
                'Access-Control-Allow-Origin': allowed_origin,
                'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PUT,DELETE',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Credentials': 'true'
            })
        # 許可されていないオリジンの場合はCORSヘッダーを返さない（ブラウザがブロックする）
        
        # レスポンス情報をログに記録
        logger.info(f"Response: {json.dumps(response)}")
        
        return response
        
    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {str(e)}")
        # エラーレスポンスにもCORSヘッダーを追加（許可されたオリジンのみ）
        allowed_origin = get_allowed_origin(event)
        error_headers = {
            'Content-Type': 'application/json'
        }
        if allowed_origin:
            error_headers.update({
                'Access-Control-Allow-Origin': allowed_origin,
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Credentials': 'true'
            })
        
        return {
            'statusCode': 500,
            'headers': error_headers,
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': str(e)
            })
        }
