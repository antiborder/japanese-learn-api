import json
import logging
import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get root_path from environment variable (empty for local development)
ROOT_PATH = os.getenv('ROOT_PATH', '')

# FastAPI application initialization
app = FastAPI(
    title="Japanese Learn API - Chat",
    description="AI Chatbot API for Japanese language learning",
    version="1.0.0",
    root_path=ROOT_PATH
)

# Import and include endpoints
from endpoints.chat import router as chat_router
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])

# Mangum handler for Lambda
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """Lambda handler for FastAPI app"""
    try:
        # Mangum handler to run FastAPI app in Lambda
        stage = event.get('requestContext', {}).get('stage', '')
        if stage:
            app.root_path = f"/{stage}"
        response = handler(event, context)
        
        # Add CORS headers to response
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

