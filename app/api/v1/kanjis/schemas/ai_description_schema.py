from pydantic import BaseModel
from typing import Optional


class KanjiAIDescriptionResponse(BaseModel):
    """
    漢字のAI解説レスポンススキーマ
    """
    kanji_id: int
    kanji_character: str
    language: str
    description: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "kanji_id": 1,
                "kanji_character": "水",
                "language": "en",
                "description": "【Basic Meaning】\n『Water is one of the fundamental elements...』"
            }
        }
