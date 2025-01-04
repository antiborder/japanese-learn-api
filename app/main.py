import json
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from app.api.v1.endpoints import word

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(word.router, prefix="/api/v1")

handler = Mangum(app)