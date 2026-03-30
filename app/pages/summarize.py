"""
app/pages/summarize.py — Document summarization page.
"""

from __future__ import annotations

import streamlit as st

from core.retrieval.summarizer import summarize_collection
from core.vectorstore.manager import VectorStoreManager


def render_summarize_page() -> None:
    """Render the summarization interface."""
    st.header("📝 Summarize Your Study Material")

    manager = VectorStoreManager()
    collections = manager.list_collections()

    if not collections:
        st.info(
            "No collections found. Upload documents from the home page to get started."
        )
        return

    # ----- collection selector -----
    col1, col2 = st.columns([3, 1])
    with col1:
        selected = st.selectbox("Select a collection", options=collections)
    with col2:
        count = manager.get_document_count(selected) if selected else 0
        st.metric("Chunks", count)

    st.markdown("---")

    # ----- summarize button -----
    if st.button("📖 Generate Summary", use_container_width=True, type="primary"):
        if not selected:
            st.warning("Please select a collection first.")
            return

        with st.spinner("Generating summary — this may take a moment…"):
            try:
                summary = summarize_collection(collection_name=selected)
            except Exception as exc:
                st.error(f"Summarization failed: {exc}")
                return

        st.markdown("### 📋 Summary")
        st.markdown(summary)

        # Store in session for download
        st.session_state["last_summary"] = summary

    # ----- download option -----
    if "last_summary" in st.session_state and st.session_state["last_summary"]:
        st.download_button(
            label="⬇️ Download Summary",
            data=st.session_state["last_summary"],
            file_name="studypal_summary.md",
            mime="text/markdown",
        )
