import os
import logging
from typing import Optional
from pydantic import BaseSettings

# ロギングの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# レベル設定
MIN_LEVEL = 1
MAX_LEVEL = 16  # N1はレベル13-16まで対応

# 級（JLPT）とレベルのマッピング
GROUP_TO_LEVELS = {
    "N5": [1, 2, 3],
    "N4": [4, 5, 6],
    "N3": [7, 8, 9],
    "N2": [10, 11, 12],
    "N1": [13, 14, 15, 16]
}

VALID_GROUPS = list(GROUP_TO_LEVELS.keys())

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