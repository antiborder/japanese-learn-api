import os
from google.cloud import texttospeech
from dotenv import load_dotenv

load_dotenv()
# 環境変数から認証情報を取得（Lambda環境ではデフォルト値を使用）
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "google-tts-key.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

tts_client = texttospeech.TextToSpeechClient()


def synthesize_sentence_speech(sentence_text: str, reading: str = None) -> bytes:
    """
    例文を音声に変換する
    
    Args:
        sentence_text: 例文テキスト（日本語）
        reading: 読み方（ひらがな、カタカナ、ローマ字など）
    
    Returns:
        音声データ（MP3形式）
    """
    # 読み方が指定されている場合はSSMLを使用
    if reading:
        # SSMLで読み方を指定（<sub>タグのalias属性を使用）
        ssml_text = f'<speak><sub alias="{reading}">{sentence_text}</sub></speak>'
        input_text = texttospeech.SynthesisInput(ssml=ssml_text)
    else:
        # 通常のテキスト入力
        input_text = texttospeech.SynthesisInput(text=sentence_text)
    
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
