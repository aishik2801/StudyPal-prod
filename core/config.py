"""
Configuration module — loads environment variables via python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class Settings:
    """Centralised application settings backed by env vars."""

    # --- API Keys ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # --- Model ---
    GROQ_MODEL_NAME: str = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

    # --- Chunking ---
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

    # --- ChromaDB ---
    CHROMA_PERSIST_DIR: str = os.getenv(
        "CHROMA_PERSIST_DIR",
        str(_PROJECT_ROOT / "data" / "chroma_db"),
    )

    # --- Uploads ---
    UPLOAD_DIR: str = str(_PROJECT_ROOT / "data" / "uploads")

    # --- Retrieval ---
    TOP_K: int = int(os.getenv("TOP_K", "5"))

    @classmethod
    def validate(cls) -> list[str]:
        """Return a list of missing-but-required config values."""
        issues: list[str] = []
        if not cls.GROQ_API_KEY:
            issues.append("GROQ_API_KEY is not set.")
        return issues


def get_settings() -> Settings:
    """Return a fresh Settings instance (re-reads env on each call)."""
    return Settings()
