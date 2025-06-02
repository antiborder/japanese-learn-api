import os
import boto3
from botocore.exceptions import ClientError
import logging
from fastapi import HTTPException
from jose import jwt
from datetime import datetime, timedelta
from schemas import UserCreate, User
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# パスワードハッシュ化の設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 環境変数の設定
cognito_client = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')
dynamodb_table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME'))
USER_POOL_ID = os.getenv('USER_POOL_ID')
CLIENT_ID = os.getenv('USER_POOL_CLIENT_ID')

# JWT設定
SECRET_KEY = "your-secret-key"  # 本番環境では環境変数から取得すべき
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def create_user(user: UserCreate) -> User:
    try:
        # パスワードをハッシュ化
        hashed_password = get_password_hash(user.password)
        
        # DynamoDBにユーザー情報を保存
        user_item = {
            'userId': user.email,  # メールアドレスをIDとして使用
            'email': user.email,
            'name': user.name,
            'hashed_password': hashed_password,  # ハッシュ化したパスワードを保存
            'is_active': True
        }
        
        dynamodb_table.put_item(Item=user_item)
        
        return User(
            id=user.email,
            email=user.email,
            name=user.name,
            is_active=True
        )
    except ClientError as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def authenticate_user(email: str, password: str):
    try:
        # ユーザー情報を取得
        response = dynamodb_table.get_item(
            Key={'userId': email}
        )
        
        if 'Item' not in response:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
            
        user = response['Item']
        
        # パスワードの検証
        if not verify_password(password, user['hashed_password']):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
            
        # JWTトークンの生成
        access_token = create_access_token(
            data={"sub": user['email']}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except ClientError as e:
        logger.error(f"Error authenticating user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_user_by_email(email: str) -> User:
    try:
        response = dynamodb_table.get_item(
            Key={'userId': email}
        )
        
        if 'Item' not in response:
            return None
            
        user_data = response['Item']
        return User(
            id=user_data['userId'],
            email=user_data['email'],
            name=user_data['name'],
            is_active=user_data.get('is_active', True)
        )
    except ClientError as e:
        logger.error(f"Error getting user by email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 