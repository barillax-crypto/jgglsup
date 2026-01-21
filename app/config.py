"""Configuration management."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration class."""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMIN_IDS: list[int] = [
        int(uid.strip()) for uid in os.getenv("TELEGRAM_ADMIN_IDS", "").split(",") if uid.strip()
    ]

    # OpenRouter
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OR_CHAT_MODEL: str = os.getenv("OR_CHAT_MODEL", "openrouter/auto")
    OR_EMBED_MODEL: str = os.getenv("OR_EMBED_MODEL", "openai/text-embedding-3-small")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Vector store
    CHROMA_PERSIST_DIR: Path = Path(os.getenv("CHROMA_PERSIST_DIR", "./data/chroma"))
    DOCS_DIR: Path = Path(os.getenv("DOCS_DIR", "./data/docs"))

    # RAG parameters
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
    RAG_SIMILARITY_THRESHOLD: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.6"))
    RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))

    # Confidentiality enforcement
    ENFORCE_CONFIDENTIALITY: bool = os.getenv("ENFORCE_CONFIDENTIALITY", "true").lower() == "true"

    # Database
    DB_PATH: Path = Path(os.getenv("DB_PATH", "./data/bot.db"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not set in .env")

    @classmethod
    def ensure_dirs(cls) -> None:
        """Create necessary directories."""
        cls.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        cls.DOCS_DIR.mkdir(parents=True, exist_ok=True)
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
