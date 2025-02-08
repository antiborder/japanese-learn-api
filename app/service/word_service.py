import boto3
import os
from fastapi import HTTPException


s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

def get_audio_from_s3(word_id: int):
    bucket_name = os.getenv("S3_BUCKET_NAME")
    object_key = f"sounds/{word_id}.mp3"  # 例: sounds/1.mp3

    try:
        # S3からオブジェクトを取得
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        audio_content = response['Body'].read()

        return audio_content  # 音声データを直接返す

    except s3_client.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail="Audio file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))