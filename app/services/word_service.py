from fastapi import HTTPException
from app.integrations import aws_integration
from app.crud import word_crud
from sqlalchemy.orm import Session
# from app.integrations.google_integration import synthesize_speech  # google.pyからインポート
import logging

logger = logging.getLogger(__name__)

def get_audio(word_id: int, db: Session):
    try:
        audio_content = aws_integration.get_word_audio_from_s3(word_id)
        return audio_content
    except HTTPException as e:
        if e.status_code == 404:  # S3に音声ファイルがない場合
            word = word_crud.get_word(db, word_id)
            # audio_content = synthesize_speech(word.hiragana) # Google Text-to-Speechを使用して音声を生成
            # aws_integration.save_word_audio_to_s3(word_id, audio_content) # 音声をS3に保存
            # return audio_content
        raise
