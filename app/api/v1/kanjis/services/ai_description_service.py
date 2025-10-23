from fastapi import HTTPException
from integrations.aws_integration import (
    check_kanji_ai_description_exists,
    get_kanji_ai_description_from_s3,
    save_kanji_ai_description_to_s3
)
from integrations.gemini_integration import generate_kanji_ai_description
import logging

logger = logging.getLogger(__name__)


def get_kanji_ai_description(kanji_id: int, kanji_character: str, lang_code: str = 'en') -> str:
    """
    漢字のAI解説を取得する
    
    処理フロー：
    1. S3にキャッシュされたAI解説が存在するかチェック
    2. 存在すればそれを返す
    3. 存在しなければGemini APIで生成
    4. 生成したAI解説をS3に保存
    5. 生成したAI解説を返す
    
    Args:
        kanji_id: 漢字ID
        kanji_character: 漢字の一文字
        lang_code: 言語コード（デフォルト: 'en'）
    
    Returns:
        AI解説テキスト
    
    Raises:
        HTTPException: 処理に失敗した場合
    """
    try:
        logger.info(f"Getting AI description for kanji_id: {kanji_id}, kanji_character: {kanji_character}, lang: {lang_code}")
        
        # ステップ1: S3にキャッシュが存在するかチェック
        if check_kanji_ai_description_exists(kanji_id, lang_code):
            # S3からキャッシュを取得
            logger.info(f"Found cached AI description in S3 for kanji_id: {kanji_id}, lang: {lang_code}")
            description_text = get_kanji_ai_description_from_s3(kanji_id, lang_code)
            return description_text
        
        # ステップ2: キャッシュが存在しない場合、Gemini APIで生成
        logger.info(f"AI description not found in S3, generating with Gemini API")
        
        if not kanji_character:
            raise HTTPException(status_code=404, detail="Kanji character is required for AI description generation")
        
        try:
            # Gemini APIでAI解説を生成
            description_text = generate_kanji_ai_description(kanji_character, lang_code)
            
            if not description_text:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate AI description: Empty response"
                )
            
            logger.info(f"Successfully generated AI description for kanji: {kanji_character}")
            
        except Exception as e:
            logger.error(f"Error generating AI description with Gemini API: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate AI description: {str(e)}"
            )
        
        # ステップ3: 生成したAI解説をS3に保存
        try:
            save_kanji_ai_description_to_s3(kanji_id, lang_code, description_text)
            logger.info(f"Successfully saved AI description to S3 for kanji_id: {kanji_id}, lang: {lang_code}")
        except Exception as e:
            # S3への保存に失敗しても、生成したテキストは返す
            logger.error(f"Error saving AI description to S3: {str(e)}")
            logger.warning("Continuing despite S3 save failure")
        
        # ステップ4: 生成したAI解説を返す
        return description_text
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_kanji_ai_description for kanji_id {kanji_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
