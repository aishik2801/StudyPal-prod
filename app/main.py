"""
app/main.py — Streamlit entry point for StudyPal.

Run with:
    streamlit run app/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path so `core.*` imports work
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

from core.constants import SUPPORTED_EXTENSIONS, DEFAULT_COLLECTION
from core.ingestion.pipeline import IngestionPipeline
from core.vectorstore.manager import VectorStoreManager
from app.pages.chat import render_chat_page
from app.pages.summarize import render_summarize_page
from app.pages.quiz import render_quiz_page
from app.pages.flashcards import render_flashcards_page
from app.pages.planner import render_planner_page


# ---- Page configuration ----
st.set_page_config(
    page_title="StudyPal — AI Study Assistant",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---- Custom CSS — dark blue premium theme ----
st.markdown(
    """
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Dark blue background */
    .stApp {
        background: linear-gradient(160deg, #0a0e27 0%, #0d1b3e 40%, #0a1628 100%);
    }

    /* Hide the default Streamlit sidebar toggle and sidebar completely */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* Hero title styling */
    .hero-title {
        text-align: center;
        font-size: 3rem;
        font-weight: 700;
        color: #ffffff;
        margin-top: 1.5rem;
        margin-bottom: 0.2rem;
        text-shadow: 0 2px 20px rgba(102, 126, 234, 0.4);
    }
    .hero-subtitle {
        text-align: center;
        font-size: 1.1rem;
        color: #8899cc;
        margin-bottom: 2rem;
        letter-spacing: 2px;
    }

    /* Upload area styling */
    .upload-section {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 0 auto 2rem auto;
        max-width: 600px;
        backdrop-filter: blur(10px);
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        border-radius: 12px;
    }
    [data-testid="stFileUploader"] label {
        color: #c0c8e0 !important;
    }

    /* Mode buttons container */
    .mode-buttons {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        margin: 1.5rem auto;
        max-width: 600px;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 12px;
        font-weight: 600;
        font-size: 1.05rem;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
        border: none;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }

    /* Headers and text in dark theme */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #e0e8ff !important;
    }
    p, .stMarkdown p, .stMarkdown li, label, .stTextInput label {
        color: #b0b8d0 !important;
    }

    /* Chat message styling */
    [data-testid="stChatMessage"] {
        border-radius: 12px;
        padding: 10px 16px;
        margin: 4px 0;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2);
    }

    /* Expanders */
    .streamlit-expanderHeader {
        border-radius: 8px;
        font-weight: 500;
        color: #c0c8e0 !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 3px;
    }

    /* Selectbox / input styling on dark background */
    .stSelectbox label, .stTextInput label, .stTextArea label {
        color: #8899cc !important;
    }

    /* Status / info / success messages */
    .stAlert {
        border-radius: 10px;
    }

    /* Download button */
    .stDownloadButton > button {
        border-radius: 10px;
    }

    /* Back button area */
    .back-btn {
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---- Session state defaults ----
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []
if "active_collection" not in st.session_state:
    st.session_state["active_collection"] = DEFAULT_COLLECTION
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "home"


def _render_home():
    """Render the simplified home page — upload + mode selection."""

    # ---- Hero header ----
    st.markdown('<div class="hero-title">StudyPal 📚</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">— AI Study Assistant —</div>',
        unsafe_allow_html=True,
    )

    # ---- File upload section ----
    allowed = [ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS]
    uploaded_files = st.file_uploader(
        "📄 Upload your study documents",
        type=allowed,
        accept_multiple_files=True,
        help="Supported formats: PDF, DOCX, TXT, PPTX",
    )

    if uploaded_files:
        if st.button("🚀 Upload & Process", use_container_width=True, type="primary"):
            collection = st.session_state["active_collection"]
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
                f"✅ Uploaded {len(results)} file(s) successfully!"
            )
            for r in results:
                emoji = "✅" if r["status"] == "success" else "❌"
                st.caption(f"{emoji} {r['source']} — {r['chunks']} chunks")

    st.markdown("")  # spacing

    # ---- Mode selection buttons ----
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("❓  Q/A Mode", use_container_width=True, type="primary"):
            st.session_state["current_page"] = "chat"
            st.rerun()
    with col2:
        if st.button("🧠  Quiz Mode", use_container_width=True, type="primary"):
            st.session_state["current_page"] = "quiz"
            st.rerun()
    with col3:
        if st.button("📇  Flashcards", use_container_width=True, type="primary"):
            st.session_state["current_page"] = "flashcards"
            st.rerun()
    with col4:
        if st.button("📝  Summarize", use_container_width=True, type="secondary"):
            st.session_state["current_page"] = "summarize"
            st.rerun()

    # Second row — Study tools
    _, col_plan, _ = st.columns([1, 2, 1])
    with col_plan:
        if st.button("📅  Daily Study Planner", use_container_width=True, type="secondary"):
            st.session_state["current_page"] = "planner"
            st.rerun()

    # ---- Show collection info at bottom ----
    manager = VectorStoreManager()
    collections = manager.list_collections()
    if collections:
        active = st.session_state["active_collection"]
        if active in collections:
            count = manager.get_document_count(active)
            st.caption(f"📊 {count} chunks loaded in current collection")
    else:
        st.caption("Upload documents to get started!")


def _render_back_button():
    """Render a back-to-home button."""
    if st.button("← Back to Home"):
        st.session_state["current_page"] = "home"
        st.rerun()


# ---- Page routing ----
page = st.session_state.get("current_page", "home")

if page == "home":
    _render_home()
elif page == "chat":
    _render_back_button()
    render_chat_page()
elif page == "quiz":
    _render_back_button()
    render_quiz_page()
elif page == "flashcards":
    _render_back_button()
    render_flashcards_page()
elif page == "planner":
    _render_back_button()
    render_planner_page()
elif page == "summarize":
    _render_back_button()
    render_summarize_page()
