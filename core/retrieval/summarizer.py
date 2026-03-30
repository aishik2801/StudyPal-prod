"""
Summarizer — map-reduce style summarization using LCEL.
"""

from __future__ import annotations

from typing import List

from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.config import get_settings
from core.vectorstore.manager import VectorStoreManager


_MAP_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a study assistant. Write a concise summary of the following text for a student.",
        ),
        ("human", "{text}"),
    ]
)

_COMBINE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are StudyPal, an AI study assistant. Combine the following summaries "
            "into a single, well-structured study summary. Use bullet points, headings, "
            "and clear language suitable for exam revision.",
        ),
        ("human", "{text}"),
    ]
)


def summarize_documents(
    documents: List[Document],
    chain_type: str = "map_reduce",
) -> str:
    """
    Summarize a list of Documents.

    For map_reduce: summarize each doc individually, then combine.
    For stuff: concatenate all docs and summarize at once.

    Args:
        documents: The documents to summarize.
        chain_type: 'map_reduce' or 'stuff'.

    Returns:
        The summary text.
    """
    settings = get_settings()

    llm = ChatGroq(
        model=settings.GROQ_MODEL_NAME,
        api_key=settings.GROQ_API_KEY,
        temperature=0.3,
    )

    parser = StrOutputParser()

    if chain_type == "stuff":
        # Single pass: concatenate everything and summarize
        combined_text = "\n\n---\n\n".join(doc.page_content for doc in documents)
        chain = _COMBINE_PROMPT | llm | parser
        return chain.invoke({"text": combined_text})

    # Map-Reduce approach
    # Step 1: Map — summarize each document individually
    map_chain = _MAP_PROMPT | llm | parser
    summaries: list[str] = []
    for doc in documents:
        summary = map_chain.invoke({"text": doc.page_content})
        summaries.append(summary)

    # Step 2: Reduce — combine all summaries into one
    combined = "\n\n".join(summaries)
    reduce_chain = _COMBINE_PROMPT | llm | parser
    return reduce_chain.invoke({"text": combined})


def summarize_collection(
    collection_name: str,
    max_chunks: int = 30,
) -> str:
    """
    Retrieve chunks from a collection and summarize them.

    Args:
        collection_name: The ChromaDB collection to summarize.
        max_chunks: Maximum number of chunks to feed into the chain.
    """
    manager = VectorStoreManager()
    # Broad query to get representative chunks
    docs = manager.similarity_search(
        query="summarize all content",
        collection_name=collection_name,
        k=max_chunks,
    )
    if not docs:
        return "No documents found in this collection."
    return summarize_documents(docs)
