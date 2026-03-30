"""
High-level vector store manager — collection CRUD and document management.
"""

from __future__ import annotations

from typing import List

import chromadb
from langchain_core.documents import Document

from core.config import get_settings
from core.constants import DEFAULT_COLLECTION
from core.vectorstore.chroma_store import get_chroma_store


class VectorStoreManager:
    """Manages ChromaDB collections and documents."""

    def __init__(self):
        self.settings = get_settings()

    # ------------------------------------------------------------------
    # Collection helpers
    # ------------------------------------------------------------------

    def list_collections(self) -> List[str]:
        """Return names of all existing collections."""
        client = chromadb.PersistentClient(path=self.settings.CHROMA_PERSIST_DIR)
        collections = client.list_collections()
        # Handle both old (returns objects) and new (returns strings) APIs
        if collections and isinstance(collections[0], str):
            return collections
        return [c.name for c in collections]

    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection by name."""
        client = chromadb.PersistentClient(path=self.settings.CHROMA_PERSIST_DIR)
        client.delete_collection(name=collection_name)

    def get_document_count(self, collection_name: str | None = None) -> int:
        """Return the number of documents (chunks) stored in a collection."""
        store = get_chroma_store(collection_name=collection_name)
        return store._collection.count()

    # ------------------------------------------------------------------
    # Document helpers
    # ------------------------------------------------------------------

    def add_documents(
        self,
        documents: List[Document],
        collection_name: str | None = None,
    ) -> None:
        """Add documents to a collection (creates it if needed)."""
        store = get_chroma_store(collection_name=collection_name)
        store.add_documents(documents)

    def similarity_search(
        self,
        query: str,
        collection_name: str | None = None,
        k: int | None = None,
    ) -> List[Document]:
        """Run a similarity search and return top-k documents."""
        k = k or self.settings.TOP_K
        store = get_chroma_store(collection_name=collection_name)
        return store.similarity_search(query, k=k)

    def clear_all(self) -> None:
        """Delete **all** collections — use with caution."""
        for name in self.list_collections():
            self.delete_collection(name)
