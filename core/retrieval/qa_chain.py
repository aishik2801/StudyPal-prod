"""
Conversational RAG QA chain — uses Groq LLM + retriever + chat memory (LCEL approach).
"""

from __future__ import annotations

from typing import List

from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from core.config import get_settings
from core.retrieval.retriever import get_retriever
from core.memory.chat_memory import get_chat_memory, clear_chat_memory


# ----- Prompts -----

_SYSTEM_PROMPT = """You are StudyPal, an AI study assistant.
Use the following pieces of context from the student's uploaded study material
to answer the question. If the context does not contain the answer,
say "I don't have enough information in your uploaded materials to answer this."
Always cite the source file and page/slide number when possible.

Context:
{context}"""

_QA_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ]
)


def _format_docs(docs: List[Document]) -> str:
    """Format retrieved documents into a single string for the prompt."""
    parts: list[str] = []
    for doc in docs:
        meta = doc.metadata
        source = meta.get("source", "unknown")
        page = meta.get("page", meta.get("slide", ""))
        header = f"[{source}" + (f", p.{page}]" if page else "]")
        parts.append(f"{header}\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def ask_question(
    question: str,
    collection_name: str | None = None,
    session_id: str = "default",
) -> dict:
    """
    Ask a question and get an answer + source documents.

    Returns:
        dict with keys: answer, source_documents
    """
    settings = get_settings()

    llm = ChatGroq(
        model=settings.GROQ_MODEL_NAME,
        api_key=settings.GROQ_API_KEY,
        temperature=0.3,
    )

    retriever = get_retriever(collection_name=collection_name)
    memory = get_chat_memory(session_id=session_id)

    # Retrieve relevant docs
    source_documents = retriever.invoke(question)

    # Build the chain using LCEL
    chain = _QA_PROMPT | llm | StrOutputParser()

    # Get chat history from memory (InMemoryChatMessageHistory)
    history = memory.messages if memory.messages else []

    answer = chain.invoke(
        {
            "context": _format_docs(source_documents),
            "chat_history": history,
            "question": question,
        }
    )

    # Save to memory
    memory.add_user_message(question)
    memory.add_ai_message(answer)

    return {
        "answer": answer,
        "source_documents": source_documents,
    }
