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


def lambda_handler(event, context):
    try:
        stage = event.get("requestContext", {}).get("stage", "")
        if stage:
            app.root_path = f"/{stage}"
        response = handler(event, context)

        if "headers" not in response:
            response["headers"] = {}

        response["headers"].update(
            {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            }
        )

        return response
    except Exception as exc:  # pragma: no cover
        logger.error("Error processing hiragana request: %s", exc)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "message": str(exc)}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }


