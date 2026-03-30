"""
app/pages/flashcards.py — AI Flashcard Mode page for StudyPal.
"""

from __future__ import annotations

import random
import streamlit as st

from core.retrieval.flashcard_engine import generate_flashcards
from core.vectorstore.manager import VectorStoreManager


# ---- Card flip CSS ----
_CARD_CSS = """
<style>
.flashcard-container {
    perspective: 1000px;
    width: 100%;
    max-width: 640px;
    height: 240px;
    margin: 1.5rem auto;
}
.flashcard {
    width: 100%;
    height: 100%;
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    text-align: center;
    font-size: 1.25rem;
    font-weight: 500;
    line-height: 1.6;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.25);
    transition: background 0.3s ease;
}
.flashcard-front {
    background: linear-gradient(135deg, #1a1f4e 0%, #1e2a6e 100%);
    border: 1px solid rgba(102, 126, 234, 0.4);
    color: #e0e8ff;
}
.flashcard-back {
    background: linear-gradient(135deg, #1a3a2a 0%, #1e4d38 100%);
    border: 1px solid rgba(52, 211, 153, 0.4);
    color: #d1fae5;
}
.card-category {
    text-align: center;
    font-size: 0.78rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #667eea;
    margin-bottom: 0.5rem;
    font-weight: 600;
}
.card-counter {
    text-align: center;
    color: #8899cc;
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
}
.card-label {
    text-align: center;
    font-size: 0.75rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
    font-weight: 600;
}
.label-front { color: #667eea; }
.label-back  { color: #34d399; }
</style>
"""


def _render_flashcard_setup() -> None:
    """Render the flashcard configuration panel."""
    st.header("📇 Flashcard Mode")
    st.caption("Generate AI-powered flashcards from your study materials")

    manager = VectorStoreManager()
    collections = manager.list_collections()

    if not collections:
        st.info("No documents found. Upload study materials from the home page first!")
        return

    collection = st.session_state.get("active_collection", "studypal_default")
    count = manager.get_document_count(collection) if collection in collections else 0
    st.caption(f"📊 {count} chunks available in current collection")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input(
            "📖 Topic / Focus Area",
            placeholder="e.g. cell biology, chapter 2, key terms…",
            help="Leave blank to cover all uploaded material",
        )
    with col2:
        num_cards = st.selectbox(
            "🃏 Number of Cards",
            options=[10, 20, 30],
            index=0,
        )

    if st.button("✨ Generate Flashcards", use_container_width=True, type="primary"):
        topic_query = topic.strip() if topic.strip() else "all key concepts and topics"

        with st.spinner("Generating your flashcards…"):
            try:
                cards = generate_flashcards(
                    topic=topic_query,
                    collection_name=collection,
                    num_cards=num_cards,
                )
            except Exception as exc:
                st.error(f"Flashcard generation failed: {exc}")
                return

        if not cards:
            st.warning("Could not generate flashcards. Try a different topic or upload more material.")
            return

        st.session_state["flashcards"] = cards
        st.session_state["fc_index"] = 0
        st.session_state["fc_flipped"] = False
        st.session_state["fc_reviewed"] = set()
        st.rerun()


def _render_flashcards() -> None:
    """Render the interactive flashcard viewer."""
    cards = st.session_state["flashcards"]
    idx = st.session_state.get("fc_index", 0)
    flipped = st.session_state.get("fc_flipped", False)
    reviewed = st.session_state.get("fc_reviewed", set())

    total = len(cards)
    card = cards[idx]
    reviewed.add(idx)
    st.session_state["fc_reviewed"] = reviewed

    st.header("📇 Flashcard Mode")

    # progress
    progress_val = len(reviewed) / total
    st.progress(progress_val)
    st.markdown(
        f'<div class="card-counter">Card {idx + 1} of {total} &nbsp;|&nbsp; '
        f'{len(reviewed)} reviewed</div>',
        unsafe_allow_html=True,
    )

    # inject CSS
    st.markdown(_CARD_CSS, unsafe_allow_html=True)

    # Category badge
    category = card.get("category", "")
    if category:
        st.markdown(
            f'<div class="card-category">🏷️ {category}</div>',
            unsafe_allow_html=True,
        )

    # Card face
    if not flipped:
        st.markdown('<div class="card-label label-front">❓ Question / Term</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="flashcard-container"><div class="flashcard flashcard-front">'
            f'{card["front"]}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="card-label label-back">✅ Answer / Definition</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="flashcard-container"><div class="flashcard flashcard-back">'
            f'{card["back"]}</div></div>',
            unsafe_allow_html=True,
        )

    # Flip button
    flip_label = "🔄 Reveal Answer" if not flipped else "🔄 Hide Answer"
    if st.button(flip_label, use_container_width=True, type="primary"):
        st.session_state["fc_flipped"] = not flipped
        st.rerun()

    st.markdown("---")

    # Navigation row
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Previous", use_container_width=True, disabled=(idx == 0)):
            st.session_state["fc_index"] = idx - 1
            st.session_state["fc_flipped"] = False
            st.rerun()
    with col2:
        if st.button("🔀 Shuffle", use_container_width=True):
            shuffled = cards[:]
            random.shuffle(shuffled)
            st.session_state["flashcards"] = shuffled
            st.session_state["fc_index"] = 0
            st.session_state["fc_flipped"] = False
            st.rerun()
    with col3:
        if st.button("➡️ Next", use_container_width=True, disabled=(idx == total - 1)):
            st.session_state["fc_index"] = idx + 1
            st.session_state["fc_flipped"] = False
            st.rerun()

    # Completion state
    if len(reviewed) == total:
        st.success("🎉 You've reviewed all flashcards! Great work.")

    # New deck button
    st.markdown("")
    if st.button("🃏 Generate New Deck", use_container_width=True, type="secondary"):
        for key in ("flashcards", "fc_index", "fc_flipped", "fc_reviewed"):
            st.session_state.pop(key, None)
        st.rerun()


def render_flashcards_page() -> None:
    """Main entry point — renders setup or active flashcard viewer."""
    if "flashcards" in st.session_state and st.session_state["flashcards"]:
        _render_flashcards()
    else:
        _render_flashcard_setup()
