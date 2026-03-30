"""
Ingestion pipeline — orchestrates load → chunk → embed → store.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List

from core.config import get_settings
from core.constants import DEFAULT_COLLECTION
from core.ingestion.loader import load_document
from core.ingestion.chunking import chunk_documents
from core.vectorstore.manager import VectorStoreManager


class IngestionPipeline:
    """End-to-end pipeline: file(s) → ChromaDB collection."""

    def __init__(self, collection_name: str | None = None):
        self.settings = get_settings()
        self.collection_name = collection_name or DEFAULT_COLLECTION
        self.manager = VectorStoreManager()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest_file(self, file_path: str) -> dict:
        """
        Ingest a single file into the vector store.

        Returns:
            Dict with keys: source, chunks, status.
        """
        docs = load_document(file_path)
        chunks = chunk_documents(docs)

        if not chunks:
            raise ValueError(
                f"No text content could be extracted from "
                f"'{os.path.basename(file_path)}'. "
                f"The file may be empty, image-only, or corrupted."
            )

        self.manager.add_documents(chunks, collection_name=self.collection_name)
        return {
            "source": os.path.basename(file_path),
            "chunks": len(chunks),
            "status": "success",
        }

    def ingest_files(self, file_paths: List[str]) -> List[dict]:
        """Ingest multiple files. Returns per-file result dicts."""
        results: List[dict] = []
        for fp in file_paths:
            try:
                results.append(self.ingest_file(fp))
            except Exception as exc:
                results.append(
                    {
                        "source": os.path.basename(fp),
                        "chunks": 0,
                        "status": f"error: {exc}",
                    }
                )
        return results

    def save_uploaded_file(self, uploaded_file) -> str:
        """
        Persist a Streamlit UploadedFile to disk and return the path.
        """
        upload_dir = Path(self.settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest = upload_dir / uploaded_file.name
        with open(dest, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return str(dest)
