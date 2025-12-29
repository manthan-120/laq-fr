"""
Configuration management for FastAPI application.
Wraps the existing config module and adds API-specific settings.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API configuration settings."""

    # API Settings
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "LAQ RAG API"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # File Upload
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR: Path = Path("./uploads")

    # Database
    DB_PATH: str = "./laq_db"
    COLLECTION_NAME: str = "laqs"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "mistral"
    EMBEDDING_MODEL: str = "nomic-embed-text"

    # RAG Settings
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.6
    TEMPERATURE: float = 0.1

    # ✅ Pydantic v2 config
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow",  # 🔑 THIS FIXES YOUR ERROR
        protected_namespaces=(),  # silences model_ warnings (optional)
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
