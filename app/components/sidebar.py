"""
app/components/sidebar.py — Sidebar with file upload, collection selector, and navigation.
"""

from __future__ import annotations

import streamlit as st

from core.constants import SUPPORTED_EXTENSIONS, DEFAULT_COLLECTION
from core.ingestion.pipeline import IngestionPipeline
from core.vectorstore.manager import VectorStoreManager


def render_sidebar() -> str:
    """
    Render the application sidebar and return the selected page name.
    """
    with st.sidebar:
        st.markdown("## 📖 StudyPal")
        st.caption("AI-Powered Study Assistant")
        st.markdown("---")

        # ----- Navigation -----
        page = st.radio(
            "Navigate",
            options=["💬 Chat", "📝 Summarize", "⚙️ Settings"],
            index=0,
            label_visibility="collapsed",
        )

        st.markdown("---")

        # ----- Collection selector -----
        manager = VectorStoreManager()
        collections = manager.list_collections()

        if collections:
            selected = st.selectbox(
                "📁 Active Collection",
                options=collections,
                index=0,
            )
        else:
            selected = DEFAULT_COLLECTION
            st.info("No collections yet — upload files to get started.")

        st.session_state["active_collection"] = selected

        st.markdown("---")

        # ----- File uploader -----
        st.markdown("### 📤 Upload Documents")
        allowed = [ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS]
        uploaded_files = st.file_uploader(
            "Upload study materials",
            type=allowed,
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

        # Optional collection name for new uploads
        new_collection = st.text_input(
            "Collection name (optional)",
            value=selected,
            help="Group related documents together.",
        )

        if st.button("🚀 Process & Upload", use_container_width=True):
            if not uploaded_files:
                st.warning("Please select at least one file.")
            else:
                collection = new_collection.strip() or DEFAULT_COLLECTION
                pipeline = IngestionPipeline(collection_name=collection)

                progress = st.progress(0)
                results = []
                for i, uf in enumerate(uploaded_files):
                    with st.spinner(f"Processing {uf.name}…"):
                        path = pipeline.save_uploaded_file(uf)
                        res = pipeline.ingest_file(path)
                        results.append(res)
                    progress.progress((i + 1) / len(uploaded_files))

                st.success(
                    f"✅ Uploaded {len(results)} file(s) → collection **{collection}**"
                )
                for r in results:
                    emoji = "✅" if r["status"] == "success" else "❌"
                    st.caption(f"{emoji} {r['source']} — {r['chunks']} chunks")

                # Refresh
                st.rerun()

        # ----- Document count -----
        if selected in collections:
            count = manager.get_document_count(selected)
            st.caption(f"📊 **{count}** chunks in *{selected}*")

    return page
