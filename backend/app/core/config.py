# app/core/config.py (SQLite version)
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database (SQLite - file-based)
    DATABASE_PATH: str = "code_evolution.db"

    # Redis (optional)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"
    REDIS_DB: str = "0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_MAX_CONNECTIONS: str = "10"

    # ChromaDB (optional)
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_DB_PATH: str = "./chroma_db"
    
    # Ollama (optional)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "codellama:7b"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

    # OpenAI (optional)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_API_BASE: Optional[str] = None
    OPENAI_MAX_TOKENS: str = "2000"

    # Anthropic (optional)
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"

    # Amazon Bedrock (optional)
    BEDROCK_MODEL_ID: Optional[str] = None
    BEDROCK_REGION: Optional[str] = None

    # Google Vertex (optional)
    VERTEX_MODEL: Optional[str] = None
    VERTEX_SERVICE_ACCOUNT_JSON: Optional[str] = None

    # Provider orchestration
    AI_PROVIDER_PRIORITY: str = "ollama,openai,anthropic"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # App settings
    APP_NAME: str = "Code Evolution Tracker"
    DEBUG: bool = True
    VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"
    API_VERSION: str = "v1"
    
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "code_evolution_ai"
    MONGODB_MAX_POOL_SIZE: str = "20"
    MONGODB_MIN_POOL_SIZE: str = "5"
    MONGODB_MAX_IDLE_TIME_MS: str = "30000"
    MONGODB_SERVER_SELECTION_TIMEOUT_MS: str = "5000"
    MONGODB_CONNECT_TIMEOUT_MS: str = "10000"
    MONGODB_SOCKET_TIMEOUT_MS: str = "30000"
    MONGODB_WRITE_CONCERN: str = "majority"
    MONGODB_READ_PREFERENCE: str = "primary"
    MONGODB_HEARTBEAT_FREQUENCY_MS: str = "10000"
    MONGODB_ENABLE_MONITORING: str = "true"
    
    # GitHub (optional)
    GITHUB_TOKEN: Optional[str] = None
    
    # Security settings for secret scanning
    ENABLE_SECRET_SCANNING: bool = True
    ALLOW_SECRET_BYPASS: bool = False  # Set to True to allow bypassing secret detection
    
    # Alert settings
    ALERT_EMAIL_RECIPIENTS: str = "admin@example.com"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields from environment variables


settings = Settings()
