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
    "s3",
    region_name=aws_region
)
logger.info("S3 client initialized with credentials")


# ============================================
# AI解説関連の関数
# ============================================

def check_kanji_ai_description_exists(kanji_id: int, lang_code: str) -> bool:
    """
    S3に漢字のAI解説が存在するかチェック
    
    Args:
        kanji_id: 漢字ID
        lang_code: 言語コード（例：'en', 'vi', 'zh', 'hi'）
    
    Returns:
        存在する場合True、存在しない場合False
    """
    try:
        object_key = f"ai_descriptions/kanjis/{kanji_id}_{lang_code}.txt"
        logger.info(f"Checking if kanji AI description exists in S3: {object_key}")
        s3_client.head_object(Bucket=bucket_name, Key=object_key)
        logger.info(f"Kanji AI description found in S3: {object_key}")
        return True
    except s3_client.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            logger.info(f"Kanji AI description not found in S3: {object_key}")
            return False
        else:
            logger.error(f"Error checking kanji AI description in S3: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


def get_kanji_ai_description_from_s3(kanji_id: int, lang_code: str) -> str:
    """
    S3から漢字のAI解説テキストを取得
    
    Args:
        kanji_id: 漢字ID
        lang_code: 言語コード
    
    Returns:
        AI解説テキスト
    """
    try:
        object_key = f"ai_descriptions/kanjis/{kanji_id}_{lang_code}.txt"
        logger.info(f"Getting kanji AI description from S3: {object_key}")
        
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        description_text = response["Body"].read().decode("utf-8")
        
        logger.info(f"Successfully retrieved kanji AI description from S3: {object_key}")
        return description_text
    except s3_client.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            logger.info(f"Kanji AI description not found in S3: {object_key}")
            raise HTTPException(status_code=404, detail="Kanji AI description not found")
        else:
            logger.error(f"Error getting kanji AI description from S3: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting kanji AI description from S3: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting kanji AI description from S3: {str(e)}")


def save_kanji_ai_description_to_s3(kanji_id: int, lang_code: str, description_text: str):
    """
    漢字のAI解説テキストをS3に保存
    
    Args:
        kanji_id: 漢字ID
        lang_code: 言語コード
        description_text: AI解説テキスト
    """
    try:
        object_key = f"ai_descriptions/kanjis/{kanji_id}_{lang_code}.txt"
        logger.info(f"Saving kanji AI description to S3: {object_key}")
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=description_text.encode("utf-8"),
            ContentType="text/plain; charset=utf-8"
        )
        
        logger.info(f"Kanji AI description saved successfully to S3: {object_key}")
    except Exception as e:
        logger.error(f"Error saving kanji AI description to S3: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving kanji AI description to S3: {str(e)}")
