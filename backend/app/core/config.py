# app/core/config.py (SQLite version)
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database (SQLite - file-based)
    DATABASE_PATH: str = "code_evolution.db"

    # Redis (optional)
    REDIS_URL: str = "redis://localhost:6379"

    # ChromaDB (optional)
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    # Ollama (optional)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "codellama:13b"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

    # OpenAI (optional)
    OPENAI_API_KEY: Optional[str] = None

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # App settings
    APP_NAME: str = "Code Evolution Tracker"
    DEBUG: bool = True
    VERSION: str = "1.0.0"
    # MongoDB
    MONGODB_URL: str
    # GitHub (optional)
    GITHUB_TOKEN: Optional[str] = None
    # Security settings for secret scanning
    ENABLE_SECRET_SCANNING: bool = True
    ALLOW_SECRET_BYPASS: bool = False  # Set to True to allow bypassing secret detection

    class Config:
        env_file = ".env"


settings = Settings()
