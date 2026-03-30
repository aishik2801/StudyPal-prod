"""
app/components/chat_ui.py — Chat message rendering & YouTube card display.
"""

from __future__ import annotations

import streamlit as st
from typing import List, Dict


def render_message(role: str, content: str) -> None:
    """Render a single chat message bubble."""
    with st.chat_message(role):
        st.markdown(content)


def render_chat_history(messages: List[Dict[str, str]]) -> None:
    """Render the full chat history stored in session state."""
    for msg in messages:
        render_message(msg["role"], msg["content"])


def render_sources(source_documents) -> None:
    """Render source document chips below an answer."""
    if not source_documents:
        return

    with st.expander("📚 Sources", expanded=False):
        seen = set()
        for doc in source_documents:
            meta = doc.metadata
            source = meta.get("source", "Unknown")
            page = meta.get("page", meta.get("slide", ""))
            label = f"**{source}**" + (f" — p.{page}" if page else "")
            if label not in seen:
                seen.add(label)
                st.markdown(f"- {label}")


def render_youtube_cards(videos: List[Dict[str, str]]) -> None:
    """Render YouTube recommendation cards in a row."""
    if not videos:
        return

    st.markdown("---")
    st.markdown("🎥 **Related Videos**")

    cols = st.columns(len(videos))
    for col, video in zip(cols, videos):
        with col:
            st.image(video.get("thumbnail", ""), use_container_width=True)
            st.markdown(
                f"[**{video.get('title', 'Video')}**]({video.get('url', '#')})"
            )
            st.caption(
                f"{video.get('channel', '')} • {video.get('duration', '')}"
            )
