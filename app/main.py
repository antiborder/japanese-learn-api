import json
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from app.api.v1.endpoints import word, kanji, component
from app.logging_config import setup_logging

# ログ設定を呼び出す
setup_logging()

app = FastAPI(
    title="Japanese Learn API",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    redirect_slashes=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(word.router, prefix="/api/v1")
app.include_router(kanji.router, prefix="/api/v1")
app.include_router(component.router, prefix="/api/v1")

# Mangumハンドラーの設定
handler = Mangum(
    app,
    lifespan="off"
)