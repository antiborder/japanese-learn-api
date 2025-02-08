import boto3
import os
from fastapi import HTTPException
from app.integrations.aws import get_audio
import logging

logger = logging.getLogger(__name__)


s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

def get_audio_from_s3(word_id: int):
    try:
        bucket_name = os.getenv("S3_BUCKET_NAME")
        object_key = f"sounds/{word_id}.mp3"  # 例: sounds/1.mp3
        audio_content = get_audio(bucket_name, object_key)
        return audio_content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
