import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from services.hiragana_audio_service import get_hiragana_audio_url


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{hiragana}/audio_url", response_model=dict)
async def fetch_hiragana_audio(hiragana: str):
    logger.info("Fetching hiragana audio URL for '%s'", hiragana)
    try:
        url = get_hiragana_audio_url(hiragana)
        return {"url": url}
    except HTTPException as exc:
        if exc.status_code == 404:
            return JSONResponse(status_code=404, content={"error": "Audio not found"})
        raise
    except Exception as exc:
        logger.error("Error fetching hiragana audio URL for '%s': %s", hiragana, exc)
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc


