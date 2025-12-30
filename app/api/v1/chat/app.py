import json
import logging
import os
from mangum import Mangum
from fastapi import FastAPI

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ROOT_PATH = os.getenv('ROOT_PATH', '')

app = FastAPI(
    title="Japanese Learn API - Chat",
    description="AI Chatbot API for Japanese language learning",
    version="1.0.0",
    root_path=ROOT_PATH
)

from endpoints.chat import router as chat_router
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])

handler = Mangum(app, lifespan="off")

ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'https://nihongo.cloud'
]

def get_allowed_origin(event):
    """リクエストのOriginヘッダーを確認し、許可されたオリジンの場合のみ返す"""
    headers = event.get('headers', {}) or {}
    origin = headers.get('Origin') or headers.get('origin')
    
    if origin and origin in ALLOWED_ORIGINS:
        return origin
    return None

def get_cors_headers(allowed_origin):
    """CORSヘッダーを生成"""
    return {
        'Access-Control-Allow-Origin': allowed_origin,
        'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PUT,DELETE',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Origin,Accept',
        'Access-Control-Allow-Credentials': 'true'
    }

def lambda_handler(event, context):
    try:
        http_method = event.get('httpMethod') or event.get('requestContext', {}).get('httpMethod', '')
        
        if http_method == 'OPTIONS':
            allowed_origin = get_allowed_origin(event)
            if allowed_origin:
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        **get_cors_headers(allowed_origin),
                        'Access-Control-Max-Age': '86400'
                    },
                    'body': ''
                }
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': ''
            }
        
        stage = event.get('requestContext', {}).get('stage', '')
        if stage:
            app.root_path = f"/{stage}"
        
        response = handler(event, context)
        
        if 'headers' not in response:
            response['headers'] = {}
        
        allowed_origin = get_allowed_origin(event)
        if allowed_origin:
            response['headers'].update(get_cors_headers(allowed_origin))
        
        return response
        
    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {str(e)}")
        allowed_origin = get_allowed_origin(event)
        error_headers = {'Content-Type': 'application/json'}
        if allowed_origin:
            error_headers.update(get_cors_headers(allowed_origin))
        
        return {
            'statusCode': 500,
            'headers': error_headers,
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': str(e)
            })
        }

