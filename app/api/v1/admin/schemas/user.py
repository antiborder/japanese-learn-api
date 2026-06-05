from pydantic import BaseModel
from typing import List, Optional


class AdminUserDetail(BaseModel):
    userId: str
    email: Optional[str] = None
    username: str
    status: str
    enabled: bool
    cognitoCreatedAt: str
    cognitoUpdatedAt: str
    # Settings from DynamoDB
    baseLevel: Optional[int] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    settingsCreatedAt: Optional[str] = None
    settingsUpdatedAt: Optional[str] = None
    lastLoginAt: Optional[str] = None


class AdminUsersPage(BaseModel):
    users: List[AdminUserDetail]
    total: int
    page: int
    page_size: int
    total_pages: int
