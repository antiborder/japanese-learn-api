import os
import logging
import requests
from typing import List, Optional
from google.cloud import texttospeech
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# 環境変数から認証情報を取得（Lambda環境ではデフォルト値を使用）
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "google-tts-key.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

tts_client = texttospeech.TextToSpeechClient()

# Google Custom Search API設定
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
CUSTOM_SEARCH_API_URL = "https://www.googleapis.com/customsearch/v1"


def synthesize_speech(word_name: str, reading: str = None) -> bytes:
    """
    テキストを音声に変換する
    
    Args:
        word_name: 単語名（漢字）
        reading: 読み方（ひらがな、カタカナ、ローマ字など）
    
    Returns:
        音声データ（MP3形式）
    """
    # 読み方が指定されている場合はSSMLを使用
    if reading:
        # SSMLで読み方を指定（<sub>タグのalias属性を使用）
        ssml_text = f'<speak><sub alias="{reading}">{word_name}</sub></speak>'
        input_text = texttospeech.SynthesisInput(ssml=ssml_text)
    else:
        # 通常のテキスト入力
        input_text = texttospeech.SynthesisInput(text=word_name)
    
    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP",  # 日本語
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
    )

    response = tts_client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )
    return response.audio_content


def search_images(query: str, num_results: int = 4) -> List[str]:
    """
    Google Custom Search APIを使用して画像を検索する
    
    Args:
        query: 検索クエリ（単語名）
        num_results: 取得する画像の数（デフォルト: 4）
    
    Returns:
        画像URLのリスト（最大num_results個）
    
    Raises:
        Exception: API呼び出しが失敗した場合
    """
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        logger.error("Google API credentials are not configured")
        raise ValueError("Google API credentials are not configured. Please set GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID.")
    
    try:
        # APIリクエストパラメータ
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_SEARCH_ENGINE_ID,
            'q': query,
            'searchType': 'image',  # 画像検索
            'num': num_results,  # 取得件数
            'lr': 'lang_ja',  # 日本語のみ
            'safe': 'active'  # セーフサーチ有効
        }
        
        logger.info(f"Searching images for query: {query}")
        
        # APIリクエスト
        response = requests.get(CUSTOM_SEARCH_API_URL, params=params, timeout=10)
        response.raise_for_status()
        
        # レスポンス解析
        data = response.json()
        
        # 画像URLを抽出（サムネイルURLを優先使用）
        image_urls = []
        items = data.get('items', [])
        
        for item in items[:num_results]:
            # まずサムネイルURLを試す（Googleがホストしているため安定）
            thumbnail_url = None
            if 'image' in item and 'thumbnailLink' in item['image']:
                thumbnail_url = item['image']['thumbnailLink']
            
            # サムネイルがない場合は元のリンクを使用
            image_url = thumbnail_url or item.get('link')
            
            if image_url:
                image_urls.append(image_url)
                logger.info(f"Using {'thumbnail' if thumbnail_url else 'original'} URL: {image_url}")
        
        logger.info(f"Found {len(image_urls)} images for query: {query}")
        return image_urls
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while searching images for query: {query}")
        raise Exception("Image search request timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching images for query '{query}': {str(e)}")
        raise Exception(f"Failed to search images: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error searching images: {str(e)}")
        raise


def download_image(image_url: str) -> tuple:
    """
    URLから画像をダウンロードする
    
    Args:
        image_url: 画像のURL
    
    Returns:
        (画像のバイナリデータ, 拡張子) のタプル
        失敗した場合は (None, None)
    
    """
    try:
        logger.info(f"Downloading image from: {image_url}")
        
        response = requests.get(image_url, timeout=10, stream=True)
        response.raise_for_status()
        
        # Content-Typeから拡張子を推測
        content_type = response.headers.get('Content-Type', '').lower()
        extension_map = {
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg',
            'image/png': 'png',
            'image/gif': 'gif',
            'image/webp': 'webp',
            'image/bmp': 'bmp'
        }
        
        # Content-Typeから拡張子を取得
        extension = extension_map.get(content_type)
        
        # Content-Typeがない場合、URLから拡張子を推測
        if not extension:
            url_lower = image_url.lower()
            for ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
                if f'.{ext}' in url_lower:
                    extension = ext if ext != 'jpeg' else 'jpg'
                    break
        
        # それでもない場合はデフォルトでjpg
        if not extension:
            extension = 'jpg'
        
        image_content = response.content
        logger.info(f"Successfully downloaded image, size: {len(image_content)} bytes, extension: {extension}")
        
        return (image_content, extension)
        
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout downloading image from: {image_url}")
        return (None, None)
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to download image from {image_url}: {str(e)}")
        return (None, None)
    except Exception as e:
        logger.error(f"Unexpected error downloading image: {str(e)}")
        return (None, None)