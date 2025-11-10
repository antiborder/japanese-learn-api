import json
import logging
import os

from fastapi import FastAPI
from mangum import Mangum

# ロギング設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ROOT_PATH = os.getenv("ROOT_PATH", "")

app = FastAPI(
    title="Japanese Learn API - Kana Lesson",
    description="API for kana lesson quiz attempts",
    version="1.0.0",
    root_path=ROOT_PATH,
)

from endpoints import router  # noqa: E402

app.include_router(router, prefix="/api/v1/kana-lesson", tags=["kana-lesson"])

handler = Mangum(app, lifespan="off")


def lambda_handler(event, context):
    try:
        stage = event.get("requestContext", {}).get("stage", "")
        if stage:
            app.root_path = f"/{stage}"

        response = handler(event, context)

        response.setdefault("headers", {})
        response["headers"].update(
            {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            }
        )

        return response
    except Exception as exc:
        logger.error("Error processing request: %s", exc)
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": "Internal server error",
                    "message": str(exc),
                }
            ),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
