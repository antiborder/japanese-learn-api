from fastapi import APIRouter, Depends, HTTPException, status
from schemas import UserCreate, User, Token, LoginRequest
from services.auth_service import create_user, authenticate_user, get_user_by_email
from dependencies import get_current_user_email
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """
    新規ユーザー登録エンドポイント
    """
    try:
        return await create_user(user)
    except Exception as e:
        logger.error(f"Error in register endpoint: {str(e)}")
        if "ConditionalCheckFailedException" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """
    ユーザーログインエンドポイント
    """
    try:
        return await authenticate_user(login_data.email, login_data.password)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in login endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/me", response_model=User)
async def get_current_user(email: str = Depends(get_current_user_email)):
    """
    現在のユーザー情報を取得するエンドポイント
    """
    try:
        user = await get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in get_current_user endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 