import logging
from fastapi import HTTPException

from common.utils.utils import convert_hiragana_to_romaji
from integrations.google_integration import synthesize_speech
from integrations.aws_integration import (
    check_hiragana_audio_exists,
    save_hiragana_audio_to_s3,
    generate_hiragana_presigned_url,
)


logger = logging.getLogger(__name__)


def get_hiragana_audio_url(hiragana: str) -> str:
    if not hiragana:
        raise HTTPException(status_code=400, detail="Invalid hiragana input")

    normalized_hiragana = hiragana.strip()
    if not normalized_hiragana:
        raise HTTPException(status_code=400, detail="Invalid hiragana input")

    romaji = convert_hiragana_to_romaji(normalized_hiragana)
    if not romaji:
        raise HTTPException(status_code=400, detail="Unable to convert hiragana to romaji")

    try:
        try:
            check_hiragana_audio_exists(romaji)
            logger.info("Hiragana audio already exists for '%s'", normalized_hiragana)
        except HTTPException as exc:
            if exc.status_code == 404:
                logger.info("Generating new hiragana audio for '%s'", normalized_hiragana)
                try:
                    audio_content = synthesize_speech(normalized_hiragana, normalized_hiragana)
                except Exception as gen_exc:
                    logger.error("Error synthesizing hiragana audio: %s", gen_exc)
                    raise HTTPException(status_code=500, detail=f"Error synthesizing speech: {gen_exc}") from gen_exc

                try:
                    save_hiragana_audio_to_s3(romaji, audio_content)
                except HTTPException:
                    raise
                except Exception as save_exc:
                    logger.error("Error saving hiragana audio: %s", save_exc)
                    raise HTTPException(status_code=500, detail=f"Error saving audio to S3: {save_exc}") from save_exc
            else:
                raise

        url = generate_hiragana_presigned_url(romaji)
        return url
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected error getting hiragana audio URL: %s", exc)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc


