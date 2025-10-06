"""
例文音声サービス
例文の音声生成、保存、取得を管理
"""

from fastapi import HTTPException
from integrations.aws_integration import (
    check_sentence_audio_exists, 
    save_sentence_audio_to_s3, 
    generate_sentence_presigned_url
)
from integrations.google_integration import synthesize_sentence_speech
import logging

logger = logging.getLogger(__name__)

def get_sentence_audio_url(sentence_id: int, sentence_text: str, hurigana: str) -> str:
    """
    例文の音声URLを取得（存在しない場合は生成）
    
    Args:
        sentence_id: 例文ID
        sentence_text: 例文テキスト（日本語）
        hurigana: 振り仮名（CSVのhurigana列）
    
    Returns:
        音声URL
    """
    try:
        logger.info(f"Getting audio URL for sentence_id: {sentence_id}")
        
        try:
            # S3にファイルが存在するか確認
            check_sentence_audio_exists(sentence_id)
            logger.info(f"Sentence audio file exists in S3 for sentence_id: {sentence_id}")
        except HTTPException as e:
            if e.status_code == 404:  # S3に音声ファイルがない場合
                logger.info(f"Sentence audio file not found in S3 for sentence_id: {sentence_id}, generating new audio")
                
                if not sentence_text:
                    raise HTTPException(status_code=404, detail=f"Sentence not found with id: {sentence_id}")
                
                try:
                    # CSVのhurigana列を直接使用
                    reading = hurigana
                    logger.info(f"Using hurigana from CSV for sentence {sentence_id}: {reading}")
                    
                    # 漢字と読み方を分けて音声合成
                    audio_content = synthesize_sentence_speech(sentence_text, reading)
                except Exception as e:
                    logger.error(f"Error synthesizing sentence speech: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"Error synthesizing sentence speech: {str(e)}")

                try:
                    save_sentence_audio_to_s3(sentence_id, audio_content)
                    logger.info(f"New sentence audio file generated and saved to S3 for sentence_id: {sentence_id}")
                except Exception as e:
                    logger.error(f"Error saving sentence audio to S3: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"Error saving sentence audio to S3: {str(e)}")
            else:
                raise

        # 署名付きURLを生成して返す
        try:
            url = generate_sentence_presigned_url(sentence_id)
            logger.info(f"Generated presigned URL for sentence_id: {sentence_id}")
            return url
        except Exception as e:
            logger.error(f"Error generating sentence presigned URL: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating sentence presigned URL: {str(e)}")

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in get_sentence_audio_url for sentence_id {sentence_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
