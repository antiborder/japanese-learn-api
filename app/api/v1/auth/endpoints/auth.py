from fastapi import APIRouter, Depends, HTTPException, status
from schemas import UserCreate, User, Token, LoginRequest
from services.auth_service import create_user, authenticate_user, get_user_by_email
from dependencies import get_current_user_email
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=User)
async def register(user: UserCreate):
    try:
        return await create_user(user)
    except Exception as e:
        logger.error(f"Error in register endpoint: {str(e)}")
        raise

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    try:
        return await authenticate_user(login_data.email, login_data.password)
    except Exception as e:
        logger.error(f"Error in login endpoint: {str(e)}")
        raise

@router.get("/me", response_model=User)
async def get_current_user(email: str = Depends(get_current_user_email)):
    try:
        user = await get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        logger.error(f"Error in get_current_user endpoint: {str(e)}")
        raise 