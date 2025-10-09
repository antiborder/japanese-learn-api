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


# ============================================
# 画像関連の関数
# ============================================

def check_word_images_exist(word_id: int) -> list:
    """
    S3に単語の画像が存在するかチェックし、存在する画像のキーリストを返す
    
    Args:
        word_id: 単語ID
    
    Returns:
        画像のキーリスト（例：['images/words/100/image_1.jpg', ...]）
        4枚未満の場合は空リストを返す
    """
    try:
        prefix = f"images/words/{word_id}/"
        logger.info(f"Checking if images exist in S3: {prefix}")
        
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            logger.info(f"No images found in S3 for word_id: {word_id}")
            return []
        
        # ファイルのキーリストを取得
        image_keys = [obj['Key'] for obj in response['Contents']]
        
        # 画像があるかチェック（最低1枚あれば返す）
        if len(image_keys) >= 1:
            logger.info(f"Found {len(image_keys)} images in S3 for word_id: {word_id}")
            return sorted(image_keys)[:4]  # 最大4枚
        else:
            logger.info(f"No images found in S3 for word_id: {word_id}")
            return []
            
    except Exception as e:
        logger.error(f"Error checking images in S3: {str(e)}")
        return []


def save_word_image_to_s3(word_id: int, image_index: int, image_content: bytes, extension: str):
    """
    単語の画像をS3に保存
    
    Args:
        word_id: 単語ID
        image_index: 画像のインデックス（1-4）
        image_content: 画像のバイナリデータ
        extension: ファイル拡張子（例：'jpg', 'png', 'webp'）
    """
    try:
        object_key = f"images/words/{word_id}/image_{image_index}.{extension}"
        logger.info(f"Saving image to S3: {object_key}")
        
        # Content-Typeのマッピング
        content_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'bmp': 'image/bmp'
        }
        content_type = content_type_map.get(extension.lower(), 'image/jpeg')
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=image_content,
            ContentType=content_type
        )
        logger.info(f"Image saved successfully to S3: {object_key}")
    except Exception as e:
        logger.error(f"Error saving image to S3: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving image to S3: {str(e)}")


def generate_presigned_url_for_image(image_key: str) -> str:
    """
    画像の署名付きURLを生成
    
    Args:
        image_key: S3オブジェクトキー（例：'images/words/100/image_1.jpg'）
    
    Returns:
        署名付きURL
    """
    try:
        logger.info(f"Generating presigned URL for image: {image_key}")
        
        # 拡張子からContent-Typeを判定
        extension = image_key.split('.')[-1].lower()
        content_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'bmp': 'image/bmp'
        }
        content_type = content_type_map.get(extension, 'image/jpeg')
        
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': image_key
            },
            ExpiresIn=604800  # 7日間有効
        )
        logger.info("Presigned URL generated successfully for image")
        return url
    except Exception as e:
        logger.error(f"Error generating presigned URL for image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating presigned URL: {str(e)}")