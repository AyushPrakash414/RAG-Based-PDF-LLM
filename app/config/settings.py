"""
Application configuration using Pydantic BaseSettings.

Loads environment variables from .env file and provides
validated, typed access to all configuration values.
"""

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration for the Self-Healing RAG service."""

    # --- LLM Configuration ---
    groq_api_key: str = Field(
        ...,
        description="Groq API key for LLM calls.",
    )
    groq_model: str = Field(
        default="llama-3.1-8b-instant",
        description="Groq model identifier.",
    )
    groq_temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Default temperature for Groq generation.",
    )

    # --- Qdrant Configuration ---
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant server URL.",
    )
    qdrant_api_key: str | None = Field(
        default=None,
        description="Qdrant API key (required for cloud deployments).",
    )
    qdrant_collection_name: str = Field(
        default="rag_documents",
        description="Name of the Qdrant collection.",
    )

    # --- Embedding Configuration ---
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace embedding model name.",
    )
    embedding_dimension: int = Field(
        default=384,
        description="Dimension of the embedding vectors.",
    )

    # --- Retrieval Configuration ---
    top_k: int = Field(
        default=4,
        ge=1,
        le=50,
        description="Default number of chunks to retrieve.",
    )
    similarity_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Default minimum similarity score for retrieval.",
    )

    # --- Self-Healing Configuration ---
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts for the self-healing loop.",
    )
    critic_approval_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum critic confidence to approve an answer.",
    )
    retrieval_validation_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum retrieval validator confidence.",
    )

    # --- Paths ---
    documents_dir: str = Field(
        default="documents",
        description="Directory containing source documents.",
    )
    traces_dir: str = Field(
        default="traces",
        description="Directory for storing execution traces.",
    )
    prompts_dir: str = Field(
        default="app/prompts",
        description="Directory containing prompt templates.",
    )

    # --- Logging ---
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Uses lru_cache so the .env file is read only once per process.
    """
    return Settings()
