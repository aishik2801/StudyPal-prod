"""
ChromaDB vector store wrapper using LangChain.
"""

from __future__ import annotations

from pathlib import Path

from langchain_community.vectorstores import Chroma

from core.config import get_settings
from core.embeddings.factory import get_embedding_model
from core.constants import DEFAULT_COLLECTION


def get_chroma_store(
    collection_name: str | None = None,
    persist_directory: str | None = None,
) -> Chroma:
    """
    Return a LangChain Chroma vectorstore instance.

    Args:
        collection_name: Name of the ChromaDB collection.
        persist_directory: Disk path for persistent storage.
    """
    settings = get_settings()
    collection = collection_name or DEFAULT_COLLECTION
    persist_dir = persist_directory or settings.CHROMA_PERSIST_DIR

    # Ensure the directory exists
    Path(persist_dir).mkdir(parents=True, exist_ok=True)

    embedding_fn = get_embedding_model()

    return Chroma(
        collection_name=collection,
        embedding_function=embedding_fn,
        persist_directory=persist_dir,
    )
