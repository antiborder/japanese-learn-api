import boto3
import logging
import os
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

bucket_name = os.getenv("S3_BUCKET_NAME")
aws_region = os.getenv("AWS_REGION", "ap-northeast-1")

s3_client = boto3.client("s3", region_name=aws_region)


def _build_object_key(romaji: str) -> str:
    sanitized = romaji.strip().lower()
    return f"sounds/hiragana/{sanitized}.mp3"


def check_hiragana_audio_exists(romaji: str) -> bool:
    object_key = _build_object_key(romaji)
    try:
        logger.info("Checking if hiragana audio exists in S3: %s", object_key)
        s3_client.head_object(Bucket=bucket_name, Key=object_key)
        return True
    except s3_client.exceptions.ClientError as exc:  # type: ignore[attr-defined]
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code == "404":
            logger.info("Hiragana audio not found in S3: %s", object_key)
            raise HTTPException(status_code=404, detail="Audio file not found") from exc
        logger.error("Error checking hiragana audio in S3: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def save_hiragana_audio_to_s3(romaji: str, audio_content: bytes) -> None:
    object_key = _build_object_key(romaji)
    try:
        logger.info("Saving hiragana audio to S3: %s", object_key)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=audio_content,
            ContentType="audio/mpeg",
        )
        logger.info("Successfully saved hiragana audio to S3: %s", object_key)
    except Exception as exc:
        logger.error("Error saving hiragana audio to S3: %s", exc)
        raise HTTPException(status_code=500, detail=f"Error saving audio to S3: {exc}") from exc


def generate_hiragana_presigned_url(romaji: str) -> str:
    object_key = _build_object_key(romaji)
    try:
        logger.info("Generating presigned URL for hiragana audio: %s", object_key)
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket_name,
                "Key": object_key,
                "ResponseContentType": "audio/mpeg",
                "ResponseContentDisposition": f"inline; filename=hiragana_{romaji}.mp3",
            },
            ExpiresIn=3600,
        )
        logger.info("Generated presigned URL for hiragana audio")
        return url
    except Exception as exc:
        logger.error("Error generating presigned URL for hiragana audio: %s", exc)
        raise HTTPException(status_code=500, detail=f"Error generating presigned URL: {exc}") from exc


