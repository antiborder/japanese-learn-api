import google.generativeai as genai
import os
from fastapi import HTTPException
import logging
from dotenv import load_dotenv
from .section_headers import get_section_headers
from .prompts import create_description_prompt

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
    'zh-hans': 'Chinese',
    'ko': 'Korean',
    'id': 'Indonesian',
    'hi': 'Hindi',
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




def generate_ai_description(word_name: str, word_hiragana: str, lang_code: str) -> str:
    """
    Gemini APIを使用してAI解説を生成
    
    Args:
        word_name: 単語名（日本語）
        word_hiragana: 単語の読み（ひらがな）
        lang_code: 言語コード（例：'en', 'vi', 'zh', 'hi'）
    
    Returns:
        生成されたAI解説テキスト
    
    Raises:
        HTTPException: API呼び出しが失敗した場合
    """
    try:
        if not gemini_api_key:
            raise HTTPException(
                status_code=500, 
                detail="GEMINI_API_KEY is not configured"
            )
        
        logger.info(f"Generating AI description for word: {word_name} in language: {lang_code}")
        
        # Gemini 2.5 Flash-Liteモデルを使用
        # 注: 実際のモデル名は"gemini-2.5-flash-lite"の可能性があります
        # リリース時の正式なモデル名に応じて調整が必要です
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        
        # プロンプトを作成
        language_name = get_language_name(lang_code)
        headers = get_section_headers(lang_code)
        prompt = create_description_prompt(word_name, word_hiragana, language_name, headers)
        
        # AI解説を生成
        response = model.generate_content(prompt)
        
        if not response.text:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate AI description: Empty response"
            )
        
        logger.info(f"Successfully generated AI description for word: {word_name}")
        return response.text
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating AI description: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate AI description: {str(e)}"
        )


