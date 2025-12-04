import json
import logging
import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException

# Logging configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get root_path from environment variable (empty for local development)
ROOT_PATH = os.getenv('ROOT_PATH', '')

# FastAPI application initialization
app = FastAPI(
    title="Japanese Learn API - Admin",
    description="Admin API for viewing conversation logs",
    version="1.0.0",
    root_path=ROOT_PATH
)

# Import and include endpoints
from endpoints.chat_conversations import router as conversations_router
app.include_router(conversations_router, prefix="/api/v1/admin/chat", tags=["admin", "chat"])

# Note: common module will be copied during build process (prepare-build step)

# Mangum handler for Lambda
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """Lambda handler for admin API"""
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

