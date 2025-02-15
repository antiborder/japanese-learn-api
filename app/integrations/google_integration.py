# import os
# from google.cloud import texttospeech
# from dotenv import load_dotenv

# load_dotenv()
# # 環境変数から認証情報を取得
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# tts_client = texttospeech.TextToSpeechClient()


# def synthesize_speech(word_name: str) -> bytes:
#     input_text = texttospeech.SynthesisInput(text=word_name)
#     voice = texttospeech.VoiceSelectionParams(
#         language_code="ja-JP",  # 日本語
#         ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
#     )
#     audio_config = texttospeech.AudioConfig(
#         audio_encoding=texttospeech.AudioEncoding.MP3,
#     )

#     response = tts_client.synthesize_speech(
#         input=input_text, voice=voice, audio_config=audio_config
#     )
#     return response.audio_content