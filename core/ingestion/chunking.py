"""
Text chunking — wraps LangChain's RecursiveCharacterTextSplitter.
"""

from __future__ import annotations

from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.config import get_settings


def chunk_documents(
    documents: List[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> List[Document]:
    """
    Split a list of Documents into smaller chunks.

    Args:
        documents: Source documents from the loader.
        chunk_size: Maximum characters per chunk (default from config).
        chunk_overlap: Overlap between consecutive chunks (default from config).

    Returns:
        List of chunked Documents with inherited metadata.
    """
    settings = get_settings()
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    # Filter out empty / whitespace-only chunks that would produce
    # empty embeddings and cause ChromaDB to reject the upsert.
    chunks = [c for c in chunks if c.page_content and c.page_content.strip()]

    return chunks
