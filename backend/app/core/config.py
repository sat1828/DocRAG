"""
Application configuration settings.
All environment variables are loaded and validated here.
"""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/rag_db"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@postgres:5432/rag_db"

    # Ollama
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.3:8b"

    # JWT Authentication
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./data/chroma"

    # File Upload
    MAX_PDF_PAGES: int = 100
    MAX_FILE_SIZE_MB: int = 50

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Environment
    ENVIRONMENT: str = "development"

    # BM25 + Hybrid Search
    BM25_ENABLED: bool = True

    # Cross-Encoder Reranking
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    model_config = ConfigDict(env_file=".env", case_sensitive=True)


# Global settings instance
settings = Settings()
