import json
import logging
import os
from mangum import Mangum
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ROOT_PATH = os.getenv("ROOT_PATH", "")

app = FastAPI(
    title="Japanese Learn API - Hiragana",
    description="API for managing hiragana audio",
    version="1.0.0",
    root_path=ROOT_PATH,
)

from endpoints.hiragana import router

app.include_router(router, prefix="/api/v1/hiragana", tags=["hiragana"])

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
        
        stage = event.get("requestContext", {}).get("stage", "")
        if stage:
            app.root_path = f"/{stage}"
        response = handler(event, context)

        # レスポンスにCORSヘッダーを追加（許可されたオリジンのみ）
        if "headers" not in response:
            response["headers"] = {}

        allowed_origin = get_allowed_origin(event)
        if allowed_origin:
            response["headers"].update({
                'Access-Control-Allow-Origin': allowed_origin,
                'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PUT,DELETE',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Credentials': 'true'
            })
        # 許可されていないオリジンの場合はCORSヘッダーを返さない（ブラウザがブロックする）

        # レスポンス情報をログに記録
        logger.info(f"Response: {json.dumps(response)}")

        return response
    except Exception as exc:  # pragma: no cover
        logger.error(f"Unexpected error in lambda_handler: {str(exc)}")
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
            "statusCode": 500,
            "headers": error_headers,
            "body": json.dumps({
                "error": "Internal Server Error",
                "message": str(exc)
            })
        }


