import boto3
import os
from fastapi import HTTPException
import logging
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

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

def check_sentence_audio_exists(sentence_id: int) -> bool:
    try:
        object_key = f"sounds/sentences/{sentence_id}.mp3"
        logger.info(f"Checking if sentence audio exists in S3: {object_key}")
        s3_client.head_object(Bucket=bucket_name, Key=object_key)
        return True
    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            logger.info(f"Sentence audio file not found in S3: {object_key}")
            raise HTTPException(status_code=404, detail="Sentence audio file not found")
        else:
            logger.error(f"Error checking sentence audio file in S3: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

def save_sentence_audio_to_s3(sentence_id: int, audio_content: bytes):
    try:
        object_key = f"sounds/sentences/{sentence_id}.mp3"
        logger.info(f"Saving sentence audio to S3: {object_key}")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=audio_content,
            ContentType='audio/mpeg'
        )
        logger.info(f"Sentence audio saved successfully to S3: {object_key}")
    except Exception as e:
        logger.error(f"Error saving sentence audio to S3: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving sentence audio to S3: {str(e)}")

def generate_sentence_presigned_url(sentence_id: int) -> str:
    try:
        object_key = f"sounds/sentences/{sentence_id}.mp3"
        logger.info(f"Generating presigned URL for sentence: {object_key}")
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_key,
                'ResponseContentType': 'audio/mpeg',
                'ResponseContentDisposition': f'inline; filename=sentence_audio_{sentence_id}.mp3'
            },
            ExpiresIn=3600  # 1時間有効
        )
        logger.info("Sentence presigned URL generated successfully")
        return url
    except Exception as e:
        logger.error(f"Error generating sentence presigned URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating sentence presigned URL: {str(e)}")


def check_ai_description_exists(sentence_id: int, lang_code: str) -> bool:
    """
    S3にAI解説が存在するかチェック
    
    Args:
        sentence_id: 例文ID
        lang_code: 言語コード（例：'en', 'vi', 'zh', 'hi'）
    
    Returns:
        存在する場合True、存在しない場合False
    """
    try:
        object_key = f"ai_descriptions/sentences/{sentence_id}_{lang_code}.txt"
        logger.info(f"Checking if AI description exists in S3: {object_key}")
        s3_client.head_object(Bucket=bucket_name, Key=object_key)
        logger.info(f"AI description found in S3: {object_key}")
        return True
    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            logger.info(f"AI description not found in S3: {object_key}")
            return False
        else:
            logger.error(f"Error checking AI description in S3: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


def get_ai_description_from_s3(sentence_id: int, lang_code: str) -> str:
    """
    S3からAI解説テキストを取得
    
    Args:
        sentence_id: 例文ID
        lang_code: 言語コード
    
    Returns:
        AI解説テキスト
    """
    try:
        object_key = f"ai_descriptions/sentences/{sentence_id}_{lang_code}.txt"
        logger.info(f"Getting AI description from S3: {object_key}")
        
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        description_text = response['Body'].read().decode('utf-8')
        
        logger.info(f"Successfully retrieved AI description from S3: {object_key}")
        return description_text
    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.info(f"AI description not found in S3: {object_key}")
            raise HTTPException(status_code=404, detail="AI description not found")
        else:
            logger.error(f"Error getting AI description from S3: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting AI description from S3: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting AI description from S3: {str(e)}")


def save_ai_description_to_s3(sentence_id: int, lang_code: str, description_text: str):
    """
    AI解説テキストをS3に保存
    
    Args:
        sentence_id: 例文ID
        lang_code: 言語コード
        description_text: AI解説テキスト
    """
    try:
        object_key = f"ai_descriptions/sentences/{sentence_id}_{lang_code}.txt"
        logger.info(f"Saving AI description to S3: {object_key}")
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=description_text.encode('utf-8'),
            ContentType='text/plain; charset=utf-8'
        )
        
        logger.info(f"AI description saved successfully to S3: {object_key}")
    except Exception as e:
        logger.error(f"Error saving AI description to S3: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving AI description to S3: {str(e)}")
