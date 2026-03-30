"""
app/pages/chat.py — Conversational RAG chat page (Q/A Mode).
"""

from __future__ import annotations

import streamlit as st

from core.retrieval.qa_chain import ask_question
from core.recommendation.youtube import search_youtube
from core.memory.chat_memory import clear_chat_memory
from app.components.chat_ui import (
    render_chat_history,
    render_message,
    render_sources,
    render_youtube_cards,
)


def render_chat_page() -> None:
    """Render the main chat interface."""
    st.header("💬 Chat with your Study Material")

    collection = st.session_state.get("active_collection", "studypal_default")

    # ----- toolbar -----
    cols = st.columns([4, 1])
    with cols[1]:
        if st.button("🗑️ Clear Chat"):
            st.session_state["chat_messages"] = []
            st.session_state["last_youtube"] = []
            st.session_state["last_sources"] = []
            clear_chat_memory(session_id=collection)
            st.rerun()

    # ----- init session state -----
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []
    if "last_youtube" not in st.session_state:
        st.session_state["last_youtube"] = []
    if "last_sources" not in st.session_state:
        st.session_state["last_sources"] = []

    render_chat_history(st.session_state["chat_messages"])

    # ----- user input -----
    if prompt := st.chat_input("Ask a question about your study material…"):
        # Show user message immediately
        st.session_state["chat_messages"].append(
            {"role": "user", "content": prompt}
        )
        render_message("user", prompt)

        # Get RAG answer
        with st.spinner("Thinking…"):
            try:
                result = ask_question(
                    question=prompt,
                    collection_name=collection,
                    session_id=collection,
                )
                answer = result["answer"]
                sources = result.get("source_documents", [])
            except Exception as exc:
                answer = f"⚠️ Error: {exc}"
                sources = []

        # Display assistant answer
        st.session_state["chat_messages"].append(
            {"role": "assistant", "content": answer}
        )
        render_message("assistant", answer)

        # Persist sources
        st.session_state["last_sources"] = sources
        render_sources(sources)

        # YouTube recommendations — always shown in Q/A mode
        try:
            videos = search_youtube(prompt)
            st.session_state["last_youtube"] = videos
            render_youtube_cards(videos)
        except Exception as exc:
            st.warning(f"YouTube search failed: {exc}")
            st.session_state["last_youtube"] = []

    else:
        # Re-render persisted sources and YouTube on rerun
        if st.session_state.get("last_sources"):
            render_sources(st.session_state["last_sources"])
        if st.session_state.get("last_youtube"):
            render_youtube_cards(st.session_state["last_youtube"])
