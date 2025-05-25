import boto3
import os
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

# S3クライアントの設定
bucket_name = os.getenv("S3_BUCKET_NAME")
aws_region = os.getenv("AWS_REGION", "ap-northeast-1")

logger.info(f"Bucket Name: {bucket_name}")
logger.info(f"AWS Region: {aws_region}")

# AWS認証情報を使用してS3クライアントを初期化
s3_client = boto3.client(
    's3',
    region_name=aws_region
)
logger.info("S3 client initialized with credentials")

def check_word_audio_exists(word_id: int) -> bool:
    try:
        object_key = f"sounds/words/{word_id}.mp3"
        logger.info(f"Checking if audio exists in S3: {object_key}")
        s3_client.head_object(Bucket=bucket_name, Key=object_key)
        return True
    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            logger.info(f"Audio file not found in S3: {object_key}")
            raise HTTPException(status_code=404, detail="Audio file not found")
        else:
            logger.error(f"Error checking audio file in S3: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

def save_word_audio_to_s3(word_id: int, audio_content: bytes):
    try:
        object_key = f"sounds/words/{word_id}.mp3"
        logger.info(f"Saving audio to S3: {object_key}")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=audio_content,
            ContentType='audio/mpeg'
        )
        logger.info(f"Audio saved successfully to S3: {object_key}")
    except Exception as e:
        logger.error(f"Error saving audio to S3: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving audio to S3: {str(e)}")

def generate_presigned_url(word_id: int) -> str:
    try:
        object_key = f"sounds/words/{word_id}.mp3"
        logger.info(f"Generating presigned URL for: {object_key}")
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_key,
                'ResponseContentType': 'audio/mpeg',
                'ResponseContentDisposition': f'inline; filename=audio_{word_id}.mp3'
            },
            ExpiresIn=3600  # 1時間有効
        )
        logger.info("Presigned URL generated successfully")
        return url
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating presigned URL: {str(e)}")