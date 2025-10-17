import google.generativeai as genai
import os
from fastapi import HTTPException
import logging
from dotenv import load_dotenv
from .prompts import create_sentence_grammar_prompt

# .envファイルを読み込み
load_dotenv()

logger = logging.getLogger(__name__)

# Gemini APIの設定
gemini_api_key = os.getenv("GEMINI_API_KEY")

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    logger.info("Gemini API configured successfully")
else:
    logger.warning("GEMINI_API_KEY not found in environment variables")


# 言語名のマッピング
LANGUAGE_NAMES = {
    'en': 'English',
    'vi': 'Vietnamese',
    'zh': 'Chinese',
    'hi': 'Hindi',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'ko': 'Korean',
    'th': 'Thai',
    'id': 'Indonesian',
    'ms': 'Malay',
    'tl': 'Filipino',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ar': 'Arabic',
    'it': 'Italian',
    'nl': 'Dutch',
    'sv': 'Swedish',
    'no': 'Norwegian',
    'da': 'Danish',
    'fi': 'Finnish',
    'pl': 'Polish',
    'tr': 'Turkish',
    'he': 'Hebrew',
    'ja': 'Japanese'
}


def get_language_name(lang_code: str) -> str:
    """
    言語コードから言語名を取得
    
    Args:
        lang_code: 言語コード（例：'en', 'vi'）
    
    Returns:
        言語名（例：'English', 'Vietnamese'）
    """
    return LANGUAGE_NAMES.get(lang_code.lower(), 'English')


def generate_sentence_grammar_description(sentence_text: str, jlpt_level: str, lang_code: str) -> str:
    """
    Gemini APIを使用して例文の文法解説を生成
    
    Args:
        sentence_text: 例文テキスト（日本語）
        jlpt_level: JLPT級（例：'N5', 'N4', 'N3', 'N2', 'N1'）
        lang_code: 言語コード（例：'en', 'vi', 'zh', 'hi'）
    
    Returns:
        生成されたAI文法解説テキスト
    
    Raises:
        HTTPException: API呼び出しが失敗した場合
    """
    try:
        if not gemini_api_key:
            raise HTTPException(
                status_code=500, 
                detail="GEMINI_API_KEY is not configured"
            )
        
        logger.info(f"Generating AI grammar description for sentence: {sentence_text} at {jlpt_level} level in language: {lang_code}")
        
        # Gemini 2.0 Flash-Liteモデルを使用
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        
        # プロンプトを作成
        language_name = get_language_name(lang_code)
        prompt = create_sentence_grammar_prompt(sentence_text, jlpt_level, language_name)
        
        # AI文法解説を生成
        response = model.generate_content(prompt)
        
        if not response.text:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate AI grammar description: Empty response"
            )
        
        logger.info(f"Successfully generated AI grammar description for sentence: {sentence_text}")
        return response.text
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating AI grammar description: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate AI grammar description: {str(e)}"
        )
