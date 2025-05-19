from fastapi import HTTPException
from app.integrations import aws_integration
from app.crud import word_crud
from sqlalchemy.orm import Session
from app.integrations.google_integration import synthesize_speech
import logging

logger = logging.getLogger(__name__)

def get_audio_url(word_id: int, db: Session) -> str:
    try:
        logger.info(f"Getting audio URL for word_id: {word_id}")
        try:
            # S3にファイルが存在するか確認
            aws_integration.check_word_audio_exists(word_id)
            logger.info(f"Audio file exists in S3 for word_id: {word_id}")
        except HTTPException as e:
            if e.status_code == 404:  # S3に音声ファイルがない場合
                logger.info(f"Audio file not found in S3 for word_id: {word_id}, generating new audio")
                word = word_crud.get_word(db, word_id)
                if not word:
                    raise HTTPException(status_code=404, detail="Word not found")
                
                audio_content = synthesize_speech(word.hiragana)
                aws_integration.save_word_audio_to_s3(word_id, audio_content)
                logger.info(f"New audio file generated and saved to S3 for word_id: {word_id}")
            else:
                raise

        # 署名付きURLを生成して返す
        url = aws_integration.generate_presigned_url(word_id)
        logger.info(f"Generated presigned URL for word_id: {word_id}")
        return url

    except Exception as e:
        logger.error(f"Error in get_audio_url for word_id {word_id}: {str(e)}")
        raise
