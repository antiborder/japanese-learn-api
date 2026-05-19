from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from enum import Enum


class ContactCategory(str, Enum):
    feature_request = "feature_request"
    question = "question"
    bug_report = "bug_report"
    other = "other"


class ContactRequest(BaseModel):
    category: ContactCategory
    email: EmailStr
    subject: str
    body: str
    lang: str
    recaptcha_token: Optional[str] = None
    honeypot: Optional[str] = None

    @validator("subject")
    def subject_length(cls, v):
        if not v.strip():
            raise ValueError("Subject cannot be empty")
        if len(v) > 100:
            raise ValueError("Subject must be 100 characters or less")
        return v.strip()

    @validator("body")
    def body_length(cls, v):
        if not v.strip():
            raise ValueError("Body cannot be empty")
        if len(v) > 2000:
            raise ValueError("Body must be 2000 characters or less")
        return v.strip()


class ContactResponse(BaseModel):
    message: str
