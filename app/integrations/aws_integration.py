import boto3
import os
from fastapi import HTTPException


# S3クライアントの設定
bucket_name = os.getenv("S3_BUCKET_NAME")

if os.getenv("AWS_ACCESS_KEY") and os.getenv("AWS_SECRET_ACCESS_KEY"):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )
else:
    s3_client = boto3.client(
        's3',
        region_name=os.getenv("AWS_REGION")  # ここだけ環境変数から取得
    )

def get_word_audio_from_s3(word_id: int):
    try:
        object_key = f"sounds/words/{word_id}.mp3"
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        audio_content = response['Body'].read()
        return audio_content

    except s3_client.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail="Audio file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def save_word_audio_to_s3(word_id: int, audio_content: bytes):
    try:
        object_key = f"sounds/words/{word_id}.mp3"
        s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=audio_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))