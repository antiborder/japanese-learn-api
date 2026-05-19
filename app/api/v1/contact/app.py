import json
import logging
import os
from mangum import Mangum
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ROOT_PATH = os.getenv("ROOT_PATH", "")

app = FastAPI(
    title="Japanese Learn API - Contact",
    description="お問い合わせフォーム API",
    version="1.0.0",
    root_path=ROOT_PATH,
)

if not os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

from endpoints.contact import router
app.include_router(router, prefix="/api/v1/contact", tags=["contact"])

handler = Mangum(app, lifespan="off")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://nihongo.cloud",
]


def get_allowed_origin(event):
    headers = event.get("headers", {}) or {}
    origin = headers.get("Origin") or headers.get("origin")
    return origin if origin in ALLOWED_ORIGINS else None


def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        http_method = event.get("httpMethod") or event.get("requestContext", {}).get("httpMethod", "")
        if http_method == "OPTIONS":
            allowed_origin = get_allowed_origin(event)
            headers = {"Content-Type": "application/json"}
            if allowed_origin:
                headers.update({
                    "Access-Control-Allow-Origin": allowed_origin,
                    "Access-Control-Allow-Methods": "OPTIONS,POST",
                    "Access-Control-Allow-Headers": "Content-Type,Authorization,Origin,Accept",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "86400",
                })
            return {"statusCode": 200, "headers": headers, "body": ""}

        stage = event.get("requestContext", {}).get("stage", "")
        if stage:
            app.root_path = f"/{stage}"
        response = handler(event, context)

        if "headers" not in response:
            response["headers"] = {}
        allowed_origin = get_allowed_origin(event)
        if allowed_origin:
            response["headers"].update({
                "Access-Control-Allow-Origin": allowed_origin,
                "Access-Control-Allow-Methods": "OPTIONS,POST",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Credentials": "true",
            })

        logger.info(f"Response: {json.dumps(response)}")
        return response

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        allowed_origin = get_allowed_origin(event)
        error_headers = {"Content-Type": "application/json"}
        if allowed_origin:
            error_headers["Access-Control-Allow-Origin"] = allowed_origin
        return {
            "statusCode": 500,
            "headers": error_headers,
            "body": json.dumps({"error": "Internal Server Error"}),
        }
