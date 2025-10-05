from fastapi import HTTPException
from integrations.aws_integration import check_word_audio_exists, save_word_audio_to_s3, generate_presigned_url
from integrations.google_integration import synthesize_speech
import boto3
import os
import logging

logger = logging.getLogger(__name__)

def get_audio_url(word_id: int, word_name: str, hiragana: str) -> str:
    try:
        logger.info(f"Getting audio URL for word_id: {word_id}")
        try:
            # S3にファイルが存在するか確認
            check_word_audio_exists(word_id)
            logger.info(f"Audio file exists in S3 for word_id: {word_id}")
        except HTTPException as e:
            if e.status_code == 404:  # S3に音声ファイルがない場合
                logger.info(f"Audio file not found in S3 for word_id: {word_id}, generating new audio")
                if not hiragana:
                    raise HTTPException(status_code=404, detail=f"Word not found with id: {word_id}")
                
                try:
                    # 漢字と読み方を分けて音声合成
                    audio_content = synthesize_speech(word_name, hiragana)
                except Exception as e:
                    logger.error(f"Error synthesizing speech: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"Error synthesizing speech: {str(e)}")

                try:
                    save_word_audio_to_s3(word_id, audio_content)
                    logger.info(f"New audio file generated and saved to S3 for word_id: {word_id}")
                except Exception as e:
                    logger.error(f"Error saving audio to S3: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"Error saving audio to S3: {str(e)}")
            else:
                raise

        # 署名付きURLを生成して返す
        try:
            url = generate_presigned_url(word_id)
            logger.info(f"Generated presigned URL for word_id: {word_id}")
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating presigned URL: {str(e)}")

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in get_audio_url for word_id {word_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
