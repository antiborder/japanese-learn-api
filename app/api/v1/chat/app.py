import json
import logging
import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Logging configuration
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

# CORS middleware (only for local development)
# In Lambda environment, CORS headers are set in lambda_handler
if not os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Import and include endpoints
from endpoints.chat import router as chat_router
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])

# Mangum handler for Lambda
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """Lambda handler for FastAPI app"""
    try:
        # Use Mangum handler to run FastAPI app in Lambda
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

