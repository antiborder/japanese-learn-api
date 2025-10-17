from fastapi import HTTPException
from integrations.aws_integration import (
    check_ai_description_exists,
    get_ai_description_from_s3,
    save_ai_description_to_s3
)
from integrations.gemini_integration import generate_ai_description
import logging

logger = logging.getLogger(__name__)


def get_ai_description(word_id: int, word_name: str, word_hiragana: str, lang_code: str = 'en') -> str:
    """
    単語のAI解説を取得する
    
    処理フロー：
    1. S3にキャッシュされたAI解説が存在するかチェック
    2. 存在すればそれを返す
    3. 存在しなければGemini APIで生成
    4. 生成したAI解説をS3に保存
    5. 生成したAI解説を返す
    
    Args:
        word_id: 単語ID
        word_name: 単語名（日本語）
        word_hiragana: 単語の読み（ひらがな）
        lang_code: 言語コード（デフォルト: 'en'）
    
    Returns:
        AI解説テキスト
    
    Raises:
        HTTPException: 処理に失敗した場合
    """
    try:
        logger.info(f"Getting AI description for word_id: {word_id}, word_name: {word_name}, lang: {lang_code}")
        
        # ステップ1: S3にキャッシュが存在するかチェック
        if check_ai_description_exists(word_id, lang_code):
            # S3からキャッシュを取得
            logger.info(f"Found cached AI description in S3 for word_id: {word_id}, lang: {lang_code}")
            description_text = get_ai_description_from_s3(word_id, lang_code)
            return description_text
        
        # ステップ2: キャッシュが存在しない場合、Gemini APIで生成
        logger.info(f"AI description not found in S3, generating with Gemini API")
        
        if not word_name:
            raise HTTPException(status_code=404, detail="Word name is required for AI description generation")
        
        if not word_hiragana:
            # 読みがない場合は基本的な説明で代用
            word_hiragana = "日本語の単語"
        
        try:
            # Gemini APIでAI解説を生成
            description_text = generate_ai_description(word_name, word_hiragana, lang_code)
            
            if not description_text:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate AI description: Empty response"
                )
            
            logger.info(f"Successfully generated AI description for word: {word_name}")
            
        except Exception as e:
            logger.error(f"Error generating AI description with Gemini API: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate AI description: {str(e)}"
            )
        
        # ステップ3: 生成したAI解説をS3に保存
        try:
            save_ai_description_to_s3(word_id, lang_code, description_text)
            logger.info(f"Successfully saved AI description to S3 for word_id: {word_id}, lang: {lang_code}")
        except Exception as e:
            # S3への保存に失敗しても、生成したテキストは返す
            logger.error(f"Error saving AI description to S3: {str(e)}")
            logger.warning("Continuing despite S3 save failure")
        
        # ステップ4: 生成したAI解説を返す
        return description_text
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_ai_description for word_id {word_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


