"""
Retriever — builds a LangChain retriever from ChromaDB.
"""

from __future__ import annotations

from langchain_core.retrievers import BaseRetriever

from core.config import get_settings
from core.vectorstore.chroma_store import get_chroma_store


def get_retriever(
    collection_name: str | None = None,
    k: int | None = None,
) -> BaseRetriever:
    """
    Return a LangChain retriever backed by the Chroma vector store.

    Args:
        collection_name: Collection to search.
        k: Number of documents to retrieve.
    """
    settings = get_settings()
    k = k or settings.TOP_K
    store = get_chroma_store(collection_name=collection_name)
    return store.as_retriever(search_kwargs={"k": k})
