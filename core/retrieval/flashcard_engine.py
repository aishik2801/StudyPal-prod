"""
Flashcard Engine — generates flashcards from uploaded study materials using Groq + RAG.
"""

from __future__ import annotations

import json
import re
from typing import List, Optional

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.config import get_settings
from core.retrieval.retriever import get_retriever


# ----- Prompt -----

_FLASHCARD_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are StudyPal, an AI study assistant that creates flashcards for students.\n"
            "Using ONLY the context provided below, generate exactly {num_cards} flashcards.\n\n"
            "IMPORTANT RULES:\n"
            "- Base ALL flashcards strictly on the provided context\n"
            "- Front: a clear, concise question or term (max 20 words)\n"
            "- Back: a clear, accurate answer or definition (max 60 words)\n"
            "- Category: a short topic tag (1-3 words, e.g. 'Biology', 'Key Terms')\n"
            "- Vary the flashcard types: definitions, key concepts, cause/effect, dates, formulas\n"
            "- Return ONLY valid JSON, no markdown fences, no extra text\n\n"
            "Return a JSON array of objects with this exact structure:\n"
            '[{{"front": "...", "back": "...", "category": "..."}}]\n\n'
            "Context:\n{context}",
        ),
        ("human", "Generate flashcards about: {topic}"),
    ]
)


def _format_docs(docs) -> str:
    """Format retrieved documents into a single context string."""
    parts: list[str] = []
    for doc in docs:
        meta = doc.metadata
        source = meta.get("source", "unknown")
        page = meta.get("page", meta.get("slide", ""))
        header = f"[{source}" + (f", p.{page}]" if page else "]")
        parts.append(f"{header}\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def _parse_flashcard_json(raw: str) -> List[dict]:
    """Extract and parse the JSON array from the LLM response."""
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
    cleaned = cleaned.rstrip("`").strip()

    bracket_start = cleaned.find("[")
    bracket_end = cleaned.rfind("]")
    if bracket_start != -1 and bracket_end != -1:
        cleaned = cleaned[bracket_start : bracket_end + 1]

    return json.loads(cleaned)


def generate_flashcards(
    topic: str,
    collection_name: Optional[str] = None,
    num_cards: int = 10,
) -> List[dict]:
    """
    Generate flashcards from uploaded study materials.

    Args:
        topic: The topic or subject area to focus on.
        collection_name: ChromaDB collection to search.
        num_cards: Number of flashcards to generate (default 10).

    Returns:
        List of flashcard dicts with keys: front, back, category
    """
    settings = get_settings()

    llm = ChatGroq(
        model=settings.GROQ_MODEL_NAME,
        api_key=settings.GROQ_API_KEY,
        temperature=0.6,
    )

    retriever = get_retriever(collection_name=collection_name, k=12)
    source_docs = retriever.invoke(topic)

    if not source_docs:
        raise ValueError(
            "No documents found in the collection. "
            "Please upload study materials first."
        )

    context = _format_docs(source_docs)

    chain = _FLASHCARD_PROMPT | llm | StrOutputParser()
    raw_response = chain.invoke(
        {
            "num_cards": num_cards,
            "context": context,
            "topic": topic,
        }
    )

    cards = _parse_flashcard_json(raw_response)

    # Validate — each card must have front and back
    validated = [
        c for c in cards if c.get("front") and c.get("back")
    ]

    return validated[:num_cards]
