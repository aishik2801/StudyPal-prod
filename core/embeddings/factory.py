"""
Embedding model factory.
"""

from __future__ import annotations

from langchain_huggingface import HuggingFaceEmbeddings

from core.config import get_settings

# Module-level cache so we only load the model once per process
_CACHE: dict[str, HuggingFaceEmbeddings] = {}


def get_embedding_model(model_name: str | None = None) -> HuggingFaceEmbeddings:
    """
    Return an embedding model instance.  Results are cached by model name.

    Args:
        model_name: HuggingFace model id.  Defaults to env setting.
    """
    settings = get_settings()
    name = model_name or settings.EMBEDDING_MODEL_NAME

    if name not in _CACHE:
        _CACHE[name] = HuggingFaceEmbeddings(
            model_name=name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _CACHE[name]
