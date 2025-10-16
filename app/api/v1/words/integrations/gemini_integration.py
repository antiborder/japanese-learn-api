import google.generativeai as genai
import os
from fastapi import HTTPException
import logging
from dotenv import load_dotenv

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
}

# 各言語の見出しマッピング
SECTION_HEADERS = {
    'en': {
        'meaning': '【Meaning】',
        'examples': '【Examples】',
        'synonyms': '【Synonyms】',
        'antonyms': '【Antonyms】',
        'usage': '【Usage】',
        'sentence1': '【Example Sentence 1】',
        'sentence2': '【Example Sentence 2】',
        'etymology': '【Etymology】',
        'japanese': 'Japanese:',
        'translation': 'Translation:',
        'explanation': 'Explanation:'
    },
    'vi': {
        'meaning': '【Ý nghĩa】',
        'examples': '【Ví dụ cụ thể】',
        'synonyms': '【Từ đồng nghĩa】',
        'antonyms': '【Từ trái nghĩa】',
        'usage': '【Cách sử dụng】',
        'sentence1': '【Ví dụ câu 1】',
        'sentence2': '【Ví dụ câu 2】',
        'etymology': '【Nguồn gốc】',
        'japanese': 'Tiếng Nhật:',
        'translation': 'Bản dịch:',
        'explanation': 'Giải thích:'
    }
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


def get_section_headers(lang_code: str) -> dict:
    """
    言語コードから見出し辞書を取得
    
    Args:
        lang_code: 言語コード（例：'en', 'vi'）
    
    Returns:
        見出し辞書（デフォルトは英語）
    """
    return SECTION_HEADERS.get(lang_code.lower(), SECTION_HEADERS['en'])


def create_description_prompt(word_name: str, word_meaning: str, lang_code: str) -> str:
    """
    AI解説生成用のプロンプトを作成
    
    Args:
        word_name: 単語名（日本語）
        word_meaning: 単語の意味
        lang_code: 言語コード
    
    Returns:
        プロンプトテキスト
    """
    language_name = get_language_name(lang_code)
    headers = get_section_headers(lang_code)
    
    prompt = f"""You are a Japanese language teacher. Please provide a comprehensive explanation of the Japanese word "{word_name}" in {language_name}.

Word: {word_name}
Basic meaning: {word_meaning}

Please structure your explanation using the following format in {language_name}:

{headers['meaning']}
Explain the meaning of the word in detail.

{headers['examples']}
Provide specific examples of how this word is used (2-3 examples).

{headers['synonyms']}
List similar words or synonyms (if any).

{headers['antonyms']}
List antonyms or opposite words (if any).

{headers['usage']}
Explain when and how to use this word in conversation.

{headers['sentence1']}
・{headers['japanese']} [Japanese example sentence]
・{headers['translation']} [Translation in {language_name}]
・{headers['explanation']} [Brief explanation]

{headers['sentence2']}
・{headers['japanese']} [Japanese example sentence]
・{headers['translation']} [Translation in {language_name}]
・{headers['explanation']} [Brief explanation]

{headers['etymology']}
Explain the etymology or origin of the word (if known).

Please write the entire explanation in {language_name}, keeping the section headers as they are. Make it natural, educational, and easy to understand for learners."""

    return prompt


def generate_ai_description(word_name: str, word_meaning: str, lang_code: str) -> str:
    """
    Gemini APIを使用してAI解説を生成
    
    Args:
        word_name: 単語名（日本語）
        word_meaning: 単語の意味
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
        prompt = create_description_prompt(word_name, word_meaning, lang_code)
        
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


