from pydantic import BaseModel
from typing import Optional, List

class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # For conversation continuity
    lang: Optional[str] = "ja"  # Language for response (e.g., "ja", "en", "vi", "zh", "ko", "id", "hi")

class ChatMessageResponse(BaseModel):
    response: str
    session_id: str
    word_ids: Optional[List[int]] = None
    kanji_ids: Optional[List[int]] = None

