import os
from google.cloud import texttospeech
from dotenv import load_dotenv

load_dotenv()
# 環境変数から認証情報を取得
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

tts_client = texttospeech.TextToSpeechClient()


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