"""
Available embedding model definitions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingModelInfo:
    """Metadata about an embedding model."""

    name: str
    model_id: str
    dimension: int
    description: str


# Pre-defined models the user can choose from
AVAILABLE_MODELS: list[EmbeddingModelInfo] = [
    EmbeddingModelInfo(
        name="MiniLM-L6",
        model_id="all-MiniLM-L6-v2",
        dimension=384,
        description="Fast, lightweight model — great for most use-cases.",
    ),
    EmbeddingModelInfo(
        name="MiniLM-L12",
        model_id="all-MiniLM-L12-v2",
        dimension=384,
        description="Slightly more accurate than L6, still fast.",
    ),
    EmbeddingModelInfo(
        name="MPNet-base",
        model_id="all-mpnet-base-v2",
        dimension=768,
        description="Highest quality; slower and uses more memory.",
    ),
]


def get_model_info(model_id: str) -> EmbeddingModelInfo | None:
    """Look up model info by HuggingFace model id."""
    for m in AVAILABLE_MODELS:
        if m.model_id == model_id:
            return m
    return None
