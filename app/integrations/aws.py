import boto3
import os
from fastapi import HTTPException

# S3クライアントの設定
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

def get_word_audio(bucket_name: str, word_id: int):
    try:
        object_key = f"sounds/words/{word_id}.mp3"
        print(object_key)
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        audio_content = response['Body'].read()
        return audio_content

    except s3_client.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail="Audio file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
