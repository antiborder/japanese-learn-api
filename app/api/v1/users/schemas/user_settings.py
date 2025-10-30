from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum

class ThemeEnum(str, Enum):
    SUMMER = "Summer"
    FALL = "Fall"

class LanguageEnum(str, Enum):
    EN = "en"
    VI = "vi"
    ZH_HANS = "zh-Hans"
    KO = "ko"
    ID = "id"
    HI = "hi"

class UserSettingsBase(BaseModel):
    """ユーザー設定のベーススキーマ"""
    base_level: int = Field(..., ge=1, le=15, description="ベースレベル（1-15）")
    theme: ThemeEnum = Field(..., description="テーマ（SummerまたはFall）")
    language: LanguageEnum = Field(..., description="言語（enまたはvi）")

class UserSettingsCreate(UserSettingsBase):
    """ユーザー設定作成用スキーマ"""
    pass

class UserSettingsUpdate(BaseModel):
    """ユーザー設定更新用スキーマ（部分更新対応）"""
    base_level: int = Field(None, ge=1, le=15, description="ベースレベル（1-15）")
    theme: ThemeEnum = Field(None, description="テーマ（SummerまたはFall）")
    language: LanguageEnum = Field(None, description="言語（enまたはvi）")

class UserSettingsResponse(UserSettingsBase):
    """ユーザー設定レスポンス用スキーマ"""
    user_id: str = Field(..., description="ユーザーID")
    created_at: str = Field(..., description="作成日時")
    updated_at: str = Field(..., description="更新日時")

    class Config:
        from_attributes = True
