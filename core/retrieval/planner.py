"""
Planner Engine — generates a personalized daily study schedule using Groq + RAG.
"""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from typing import List, Optional

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.config import get_settings
from core.vectorstore.manager import VectorStoreManager


# ----- Prompt -----

_PLANNER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are StudyPal, an expert study planner. "
            "Create a personalized day-by-day study schedule for a student.\n\n"
            "Student info:\n"
            "- Exam date: {exam_date}\n"
            "- Days until exam: {days_left}\n"
            "- Daily study hours available: {hours_per_day}\n"
            "- Study days per week: {days_per_week}\n"
            "- Topics from their uploaded material: {topics}\n\n"
            "RULES:\n"
            "- Distribute topics evenly across available study days\n"
            "- Each day should have 1-3 sessions (Quiz, Flashcards, Q&A Chat, or Review)\n"
            "- Build in review days every 3-4 days to reinforce learning\n"
            "- Final 2 days before exam: full review and practice quizzes only\n"
            "- Keep session times realistic given hours_per_day\n"
            "- Return ONLY valid JSON, no markdown fences, no extra text\n\n"
            "Return a JSON array of day objects:\n"
            '[{{"day": 1, "date": "YYYY-MM-DD", "focus": "topic name", '
            '"sessions": [{{"activity": "Flashcards|Quiz|Q&A Chat|Review", '
            '"topic": "...", "duration_min": 30, "notes": "..."}}]}}]',
        ),
        ("human", "Generate my study plan starting from {start_date}."),
    ]
)


def _parse_plan_json(raw: str) -> List[dict]:
    """Extract and parse JSON from LLM response."""
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    bracket_start = cleaned.find("[")
    bracket_end = cleaned.rfind("]")
    if bracket_start != -1 and bracket_end != -1:
        cleaned = cleaned[bracket_start : bracket_end + 1]
    return json.loads(cleaned)


def _extract_topics(collection_name: Optional[str], max_chunks: int = 20) -> str:
    """Pull topic names from the vector store to inform the planner."""
    try:
        manager = VectorStoreManager()
        docs = manager.similarity_search(
            query="main topics key concepts chapters",
            collection_name=collection_name,
            k=max_chunks,
        )
        # Collect unique source file names as a proxy for topics
        sources = list({d.metadata.get("source", "Unknown") for d in docs})
        return ", ".join(sources[:10]) if sources else "General study material"
    except Exception:
        return "General study material"


def generate_study_plan(
    exam_date: date,
    collection_name: Optional[str] = None,
    hours_per_day: float = 2.0,
    days_per_week: int = 5,
) -> List[dict]:
    """
    Generate a personalized daily study schedule.

    Args:
        exam_date:       The target exam / deadline date.
        collection_name: ChromaDB collection to infer topics from.
        hours_per_day:   Available study hours per day.
        days_per_week:   Number of days per week the student can study.

    Returns:
        List of day dicts with keys: day, date, focus, sessions
    """
    today = date.today()
    days_left = (exam_date - today).days

    if days_left <= 0:
        raise ValueError("Exam date must be in the future.")

    settings = get_settings()
    llm = ChatGroq(
        model=settings.GROQ_MODEL_NAME,
        api_key=settings.GROQ_API_KEY,
        temperature=0.5,
    )

    topics = _extract_topics(collection_name)

    chain = _PLANNER_PROMPT | llm | StrOutputParser()
    raw = chain.invoke(
        {
            "exam_date": exam_date.strftime("%B %d, %Y"),
            "days_left": days_left,
            "hours_per_day": hours_per_day,
            "days_per_week": days_per_week,
            "topics": topics,
            "start_date": today.strftime("%Y-%m-%d"),
        }
    )

    plan = _parse_plan_json(raw)

    # Validate minimal structure
    validated = [
        d for d in plan
        if d.get("day") and d.get("sessions")
    ]

    return validated
