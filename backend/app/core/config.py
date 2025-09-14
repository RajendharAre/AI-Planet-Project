from pydantic import BaseModel
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    def __init__(self):
        self.ENV = os.getenv("ENV", "development")
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ai_planet.db")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini")
        self.CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.CHROMA_SERVER_API = os.getenv("CHROMA_SERVER_API")
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "8000"))

settings = Settings()

