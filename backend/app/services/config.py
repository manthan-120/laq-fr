"""Configuration management for the LAQ RAG system."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class Config:
    """Application configuration with environment variable support."""

    # Database settings
    db_path: Path = field(
        default_factory=lambda: Path(os.getenv("DB_PATH", "./laq_db"))
    )
    collection_name: str = os.getenv("COLLECTION_NAME", "laqs")

    # Model settings
    llm_model: str = os.getenv("LLM_MODEL", "mistral")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

    # Ollama settings
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "60"))

    # Retrieval settings
    search_top_k: int = int(os.getenv("SEARCH_TOP_K", "10"))
    chat_top_k: int = int(os.getenv("CHAT_TOP_K", "5"))
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))

    # Processing settings
    markdown_chunk_size: int = int(
        os.getenv("MARKDOWN_CHUNK_SIZE", "20000")
    )  # For LLM extraction only
    metadata_max_length: int = int(os.getenv("METADATA_MAX_LENGTH", "500"))
    max_embedding_tokens: int = int(os.getenv("MAX_EMBEDDING_TOKENS", "256"))  # For embedding model

    # Performance optimizations
    use_batch_embeddings: bool = (
        os.getenv("USE_BATCH_EMBEDDINGS", "true").lower() == "true"
    )
    use_enhanced_context: bool = (
        os.getenv("USE_ENHANCED_CONTEXT", "true").lower() == "true"
    )
    cache_markdown_conversions: bool = (
        os.getenv("CACHE_MARKDOWN", "true").lower() == "true"
    )
    skip_duplicate_pdfs: bool = (
        os.getenv("SKIP_DUPLICATE_PDFS", "true").lower() == "true"
    )

    # LLM generation settings
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    llm_top_p: float = float(os.getenv("LLM_TOP_P", "0.9"))

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Create database directory if it doesn't exist
        self.db_path.mkdir(parents=True, exist_ok=True)

        # Validate thresholds
        if not 0 <= self.similarity_threshold <= 1:
            raise ValueError("similarity_threshold must be between 0 and 1")

        if self.search_top_k < 1:
            raise ValueError("search_top_k must be >= 1")

        if self.chat_top_k < 1:
            raise ValueError("chat_top_k must be >= 1")

        if not 0 <= self.llm_temperature <= 2:
            raise ValueError("llm_temperature must be between 0 and 2")

        if not 0 <= self.llm_top_p <= 1:
            raise ValueError("llm_top_p must be between 0 and 1")

    def display(self) -> str:
        """Return a formatted string of the configuration."""
        return f"""
Configuration:
--------------
Database Path: {self.db_path}
Collection: {self.collection_name}
LLM Model: {self.llm_model}
Embedding Model: {self.embedding_model}
Ollama Host: {self.ollama_host}
Search Top-K: {self.search_top_k}
Chat Top-K: {self.chat_top_k}
Similarity Threshold: {self.similarity_threshold}
"""
