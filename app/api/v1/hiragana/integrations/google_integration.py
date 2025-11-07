import logging
import os

from dotenv import load_dotenv
from google.cloud import texttospeech


load_dotenv()

logger = logging.getLogger(__name__)

credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "google-tts-key.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

tts_client = texttospeech.TextToSpeechClient()


def synthesize_speech(text: str, reading: str | None = None) -> bytes:
    if reading:
        ssml_text = f'<speak><sub alias="{reading}">{text}</sub></speak>'
        input_text = texttospeech.SynthesisInput(ssml=ssml_text)
    else:
        input_text = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
    )

    logger.info("Synthesizing hiragana speech for '%s'", text)
    response = tts_client.synthesize_speech(
        input=input_text,
        voice=voice,
        audio_config=audio_config,
    )
    return response.audio_content


