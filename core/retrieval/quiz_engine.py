"""
Quiz Engine — generates quizzes from uploaded study materials using Groq + RAG.
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

_QUIZ_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are StudyPal, an AI study assistant that creates quizzes for students.\n"
            "Using ONLY the context provided below, generate exactly {num_questions} quiz questions.\n"
            "Difficulty level: {difficulty}.\n"
            "Question types to include: {question_types}.\n\n"
            "IMPORTANT RULES:\n"
            "- Base ALL questions strictly on the provided context\n"
            "- For MCQ: provide exactly 4 options labeled A, B, C, D\n"
            "- For true_false: the answer must be exactly 'True' or 'False'\n"
            "- For short_answer: the answer should be a brief phrase (1-10 words)\n"
            "- Provide a brief explanation for each correct answer\n"
            "- Return ONLY valid JSON, no markdown fences, no extra text\n\n"
            "Return a JSON array of objects with this exact structure:\n"
            '[{{"type": "mcq"|"true_false"|"short_answer", '
            '"question": "...", '
            '"options": ["A) ...", "B) ...", "C) ...", "D) ..."] or null, '
            '"correct_answer": "A"|"B"|"C"|"D" or "True"|"False" or "brief answer", '
            '"explanation": "..."}}]\n\n'
            "Context:\n{context}",
        ),
        ("human", "Generate a quiz about: {topic}"),
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


def _parse_quiz_json(raw: str) -> List[dict]:
    """
    Extract and parse the JSON array from the LLM response.
    Handles cases where the LLM wraps JSON in markdown fences.
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
    cleaned = cleaned.rstrip("`").strip()

    # Try to find a JSON array in the response
    bracket_start = cleaned.find("[")
    bracket_end = cleaned.rfind("]")
    if bracket_start != -1 and bracket_end != -1:
        cleaned = cleaned[bracket_start : bracket_end + 1]

    return json.loads(cleaned)


def generate_quiz(
    topic: str,
    collection_name: Optional[str] = None,
    num_questions: int = 5,
    difficulty: str = "Medium",
    question_types: Optional[List[str]] = None,
) -> List[dict]:
    """
    Generate a quiz from uploaded study materials.

    Args:
        topic: The topic or subject area to quiz on.
        collection_name: ChromaDB collection to search.
        num_questions: Number of questions to generate (default 5).
        difficulty: 'Easy', 'Medium', or 'Hard'.
        question_types: List of types: 'mcq', 'true_false', 'short_answer'.
                        Defaults to all three.

    Returns:
        List of question dicts with keys:
            type, question, options, correct_answer, explanation
    """
    if question_types is None:
        question_types = ["mcq", "true_false", "short_answer"]

    settings = get_settings()

    llm = ChatGroq(
        model=settings.GROQ_MODEL_NAME,
        api_key=settings.GROQ_API_KEY,
        temperature=0.7,  # Slightly higher for variety in questions
    )

    # Retrieve relevant chunks
    retriever = get_retriever(collection_name=collection_name, k=10)
    source_docs = retriever.invoke(topic)

    if not source_docs:
        raise ValueError(
            "No documents found in the collection. "
            "Please upload study materials first."
        )

    context = _format_docs(source_docs)
    types_str = ", ".join(question_types)

    # Generate quiz
    chain = _QUIZ_PROMPT | llm | StrOutputParser()
    raw_response = chain.invoke(
        {
            "num_questions": num_questions,
            "difficulty": difficulty,
            "question_types": types_str,
            "context": context,
            "topic": topic,
        }
    )

    # Parse and validate
    questions = _parse_quiz_json(raw_response)

    # Basic validation — ensure each question has required fields
    validated: list[dict] = []
    for q in questions:
        if all(k in q for k in ("type", "question", "correct_answer")):
            # Ensure options is a list for MCQ, None for others
            if q["type"] == "mcq" and not q.get("options"):
                continue  # Skip malformed MCQ
            validated.append(q)

    return validated[:num_questions]
