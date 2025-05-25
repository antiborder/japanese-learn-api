import os
import logging
from typing import Optional
from pydantic import BaseSettings

# ロギングの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class Settings(BaseSettings):
    # データベース設定
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "japanese_learn")

    # AWS設定
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-northeast-1")
    
    # ロギング設定
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    def configure_logging(self):
        logging.basicConfig(
            level=self.LOG_LEVEL,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    class Config:
        case_sensitive = True

settings = Settings()
settings.configure_logging() 