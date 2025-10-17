from fastapi import HTTPException
from integrations.aws_integration import (
    check_ai_description_exists,
    get_ai_description_from_s3,
    save_ai_description_to_s3
)
from integrations.gemini_integration import generate_sentence_grammar_description
import logging

logger = logging.getLogger(__name__)


def get_sentence_grammar_description(sentence_id: int, sentence_text: str, level: int, lang_code: str = 'en') -> str:
    """
    例文のAI文法解説を取得する
    
    処理フロー：
    1. S3にキャッシュされたAI解説が存在するかチェック
    2. 存在すればそれを返す
    3. 存在しなければGemini APIで生成
    4. 生成したAI解説をS3に保存
    5. 生成したAI解説を返す
    
    Args:
        sentence_id: 例文ID
        sentence_text: 例文テキスト（日本語）
        level: レベル（1-15）
        lang_code: 言語コード（デフォルト: 'en'）
    
    Returns:
        AI文法解説テキスト
    
    Raises:
        HTTPException: 処理に失敗した場合
    """
    try:
        logger.info(f"Getting AI grammar description for sentence_id: {sentence_id}, sentence: {sentence_text}, level: {level}, lang: {lang_code}")
        
        # レベルからJLPT級を決定
        jlpt_level = _get_jlpt_level(level)
        
        # ステップ1: S3にキャッシュが存在するかチェック
        if check_ai_description_exists(sentence_id, lang_code):
            # S3からキャッシュを取得
            logger.info(f"Found cached AI grammar description in S3 for sentence_id: {sentence_id}, lang: {lang_code}")
            description_text = get_ai_description_from_s3(sentence_id, lang_code)
            return description_text
        
        # ステップ2: キャッシュが存在しない場合、Gemini APIで生成
        logger.info(f"AI grammar description not found in S3, generating with Gemini API")
        
        if not sentence_text:
            raise HTTPException(status_code=404, detail="Sentence text is required for AI grammar description generation")
        
        try:
            # Gemini APIでAI文法解説を生成
            description_text = generate_sentence_grammar_description(sentence_text, jlpt_level, lang_code)
            
            if not description_text:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate AI grammar description: Empty response"
                )
            
            logger.info(f"Successfully generated AI grammar description for sentence: {sentence_text}")
            
        except Exception as e:
            logger.error(f"Error generating AI grammar description with Gemini API: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate AI grammar description: {str(e)}"
            )
        
        # ステップ3: 生成したAI解説をS3に保存
        try:
            save_ai_description_to_s3(sentence_id, lang_code, description_text)
            logger.info(f"Successfully saved AI grammar description to S3 for sentence_id: {sentence_id}, lang: {lang_code}")
        except Exception as e:
            # S3への保存に失敗しても、生成したテキストは返す
            logger.error(f"Error saving AI grammar description to S3: {str(e)}")
            logger.warning("Continuing despite S3 save failure")
        
        # ステップ4: 生成したAI解説を返す
        return description_text
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_sentence_grammar_description for sentence_id {sentence_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


def _get_jlpt_level(level: int) -> str:
    """
    レベルからJLPT級を決定する
    
    Args:
        level: レベル（1-15）
    
    Returns:
        JLPT級（N5, N4, N3, N2, N1）
    """
    if 1 <= level <= 3:
        return "N5"
    elif 4 <= level <= 6:
        return "N4"
    elif 7 <= level <= 9:
        return "N3"
    elif 10 <= level <= 12:
        return "N2"
    elif 13 <= level <= 15:
        return "N1"
    else:
        # デフォルトはN5
        return "N5"
