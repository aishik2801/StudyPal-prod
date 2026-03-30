"""
app/pages/settings.py — Settings & administration page.
"""

from __future__ import annotations

import streamlit as st

from core.config import get_settings
from core.vectorstore.manager import VectorStoreManager
from core.memory.chat_memory import clear_all_memory
from core.embeddings.models import AVAILABLE_MODELS


def render_settings_page() -> None:
    """Render the settings page."""
    st.header("⚙️ Settings")

    settings = get_settings()

    # ---- API Key configuration ----
    st.subheader("🔑 API Configuration")
    with st.expander("Groq API Key", expanded=not bool(settings.GROQ_API_KEY)):
        api_key = st.text_input(
            "GROQ_API_KEY",
            value=settings.GROQ_API_KEY,
            type="password",
            help="Required for chat and summarization.",
        )
        if api_key != settings.GROQ_API_KEY:
            import os

            os.environ["GROQ_API_KEY"] = api_key
            st.success("API key updated for this session.")

    st.markdown("---")

    # ---- Model selection ----
    st.subheader("🧠 Model Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("LLM Model (Groq)", value=settings.GROQ_MODEL_NAME, disabled=True)
    with col2:
        model_options = [m.model_id for m in AVAILABLE_MODELS]
        current_idx = (
            model_options.index(settings.EMBEDDING_MODEL_NAME)
            if settings.EMBEDDING_MODEL_NAME in model_options
            else 0
        )
        selected_model = st.selectbox(
            "Embedding Model",
            options=model_options,
            index=current_idx,
        )
        # Show description
        for m in AVAILABLE_MODELS:
            if m.model_id == selected_model:
                st.caption(m.description)

    st.markdown("---")

    # ---- Collection management ----
    st.subheader("📁 Collection Management")
    manager = VectorStoreManager()
    collections = manager.list_collections()

    if collections:
        for name in collections:
            col_a, col_b, col_c = st.columns([3, 1, 1])
            with col_a:
                st.markdown(f"**{name}**")
            with col_b:
                count = manager.get_document_count(name)
                st.caption(f"{count} chunks")
            with col_c:
                if st.button("🗑️", key=f"del_{name}", help=f"Delete {name}"):
                    manager.delete_collection(name)
                    st.success(f"Deleted **{name}**")
                    st.rerun()
    else:
        st.info("No collections found.")

    st.markdown("---")

    # ---- Danger zone ----
    st.subheader("⚠️ Danger Zone")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if st.button("🗑️ Clear All Collections", type="primary"):
            manager.clear_all()
            st.success("All collections deleted.")
            st.rerun()
    with col_d2:
        if st.button("🧹 Clear All Chat Memory"):
            clear_all_memory()
            st.session_state["chat_messages"] = []
            st.success("Chat memory cleared.")
