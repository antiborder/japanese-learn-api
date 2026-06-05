from fastapi import APIRouter, HTTPException, Depends, Query
import boto3
import os
import logging
from schemas.user import AdminUserDetail, AdminUsersPage
from common.auth.admin_auth import require_admin_role

logger = logging.getLogger(__name__)
router = APIRouter()

COGNITO_REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "")
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "")

cognito_client = boto3.client("cognito-idp", region_name=COGNITO_REGION)
dynamodb = boto3.resource("dynamodb", region_name=COGNITO_REGION)


def _get_table():
    if not DYNAMODB_TABLE_NAME:
        return None
    return dynamodb.Table(DYNAMODB_TABLE_NAME)


def _get_user_settings(table, user_id: str) -> dict:
    try:
        response = table.get_item(Key={"PK": f"USER#{user_id}", "SK": "SETTINGS"})
        return response.get("Item", {})
    except Exception as e:
        logger.warning(f"Failed to get settings for user {user_id}: {e}")
        return {}


@router.get("/users/count")
async def get_users_count(
    admin_user: str = Depends(require_admin_role),
):
    """Return estimated total number of users in the Cognito User Pool"""
    if not COGNITO_USER_POOL_ID:
        raise HTTPException(status_code=500, detail="COGNITO_USER_POOL_ID not configured")
    try:
        response = cognito_client.describe_user_pool(UserPoolId=COGNITO_USER_POOL_ID)
        count = response["UserPool"].get("EstimatedNumberOfUsers", 0)
        return {"count": count}
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users", response_model=AdminUsersPage)
async def list_users(
    page: int = Query(0, ge=0),
    page_size: int = Query(60, ge=1, le=100),
    admin_user: str = Depends(require_admin_role),
):
    """List all Cognito users sorted by last active date desc (admin only)"""
    if not COGNITO_USER_POOL_ID:
        raise HTTPException(status_code=500, detail="COGNITO_USER_POOL_ID not configured")

    table = _get_table()

    try:
        # Fetch all users from Cognito across all pages
        all_cognito_users = []
        kwargs: dict = {"UserPoolId": COGNITO_USER_POOL_ID, "Limit": 60}
        while True:
            response = cognito_client.list_users(**kwargs)
            all_cognito_users.extend(response.get("Users", []))
            next_token = response.get("PaginationToken")
            if not next_token:
                break
            kwargs["PaginationToken"] = next_token

        # Build full result with DynamoDB settings
        result = []
        for cu in all_cognito_users:
            username = cu.get("Username", "")
            attrs = {a["Name"]: a["Value"] for a in cu.get("Attributes", [])}
            sub = attrs.get("sub", username)
            email = attrs.get("email")
            db_key = email or sub

            settings = {}
            if table and db_key:
                settings = _get_user_settings(table, db_key)

            created_at = cu.get("UserCreateDate", "")
            updated_at = cu.get("UserLastModifiedDate", "")

            result.append(
                AdminUserDetail(
                    userId=sub,
                    email=email,
                    username=username,
                    status=cu.get("UserStatus", ""),
                    enabled=cu.get("Enabled", True),
                    cognitoCreatedAt=created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
                    cognitoUpdatedAt=updated_at.isoformat() if hasattr(updated_at, "isoformat") else str(updated_at),
                    baseLevel=settings.get("base_level"),
                    theme=settings.get("theme"),
                    language=settings.get("language"),
                    settingsCreatedAt=settings.get("created_at"),
                    settingsUpdatedAt=settings.get("updated_at"),
                    lastLoginAt=settings.get("last_login_at"),
                )
            )

        # Sort by lastLoginAt descending (None last)
        result.sort(key=lambda u: u.lastLoginAt or "", reverse=True)

        total = len(result)
        total_pages = max(1, (total + page_size - 1) // page_size)
        start = page * page_size
        page_users = result[start : start + page_size]

        return AdminUsersPage(
            users=page_users,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))
