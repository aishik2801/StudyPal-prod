"""
app/pages/quiz.py — AI Quiz Mode page for StudyPal.
"""

from __future__ import annotations

import streamlit as st

from core.retrieval.quiz_engine import generate_quiz
from core.vectorstore.manager import VectorStoreManager


def _render_quiz_setup() -> None:
    """Render the quiz configuration panel."""
    st.header("🧠 Quiz Mode")
    st.caption("Generate AI-powered quizzes from your study materials")

    manager = VectorStoreManager()
    collections = manager.list_collections()

    if not collections:
        st.info(
            "No documents found. Upload study materials from the home page first!"
        )
        return

    # Collection info
    collection = st.session_state.get("active_collection", "studypal_default")
    count = manager.get_document_count(collection) if collection in collections else 0
    st.caption(f"📊 {count} chunks available in current collection")

    st.markdown("---")

    # Quiz settings
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input(
            "📖 Topic / Focus Area",
            placeholder="e.g. photosynthesis, chapter 3, key concepts…",
            help="Leave blank to quiz on all uploaded material",
        )
    with col2:
        num_questions = st.selectbox(
            "🔢 Number of Questions",
            options=[5, 10, 15],
            index=0,
        )

    col3, col4 = st.columns(2)
    with col3:
        difficulty = st.selectbox(
            "📊 Difficulty",
            options=["Easy", "Medium", "Hard"],
            index=1,
        )
    with col4:
        q_types = st.multiselect(
            "❓ Question Types",
            options=["mcq", "true_false", "short_answer"],
            default=["mcq", "true_false", "short_answer"],
            format_func=lambda x: {
                "mcq": "Multiple Choice",
                "true_false": "True / False",
                "short_answer": "Short Answer",
            }.get(x, x),
        )

    if not q_types:
        st.warning("Please select at least one question type.")
        return

    # Generate button
    if st.button("🚀 Generate Quiz", use_container_width=True, type="primary"):
        topic_query = topic.strip() if topic.strip() else "all key concepts and topics"

        with st.spinner("Generating your quiz — this may take a moment…"):
            try:
                questions = generate_quiz(
                    topic=topic_query,
                    collection_name=collection,
                    num_questions=num_questions,
                    difficulty=difficulty,
                    question_types=q_types,
                )
            except Exception as exc:
                st.error(f"Quiz generation failed: {exc}")
                return

        if not questions:
            st.warning(
                "Could not generate questions. Try a different topic or upload more material."
            )
            return

        # Store quiz in session state
        st.session_state["quiz_questions"] = questions
        st.session_state["quiz_answers"] = {}
        st.session_state["quiz_submitted"] = False
        st.session_state["quiz_score"] = None
        st.rerun()


def _render_quiz_questions() -> None:
    """Render the active quiz for the student to answer."""
    questions = st.session_state["quiz_questions"]
    submitted = st.session_state.get("quiz_submitted", False)

    st.header("🧠 Quiz Mode")
    st.caption(f"{len(questions)} questions • Answer all and submit")
    st.markdown("---")

    # Render each question
    for i, q in enumerate(questions):
        q_num = i + 1
        q_type = q.get("type", "mcq")
        question_text = q.get("question", "")

        # Type badge
        type_labels = {
            "mcq": "📋 Multiple Choice",
            "true_false": "✅ True / False",
            "short_answer": "✍️ Short Answer",
        }
        badge = type_labels.get(q_type, q_type)

        st.markdown(f"### Q{q_num}. {question_text}")
        st.caption(badge)

        answer_key = f"q_{i}"

        if q_type == "mcq":
            options = q.get("options", [])
            if options:
                selected = st.radio(
                    f"Select your answer for Q{q_num}",
                    options=options,
                    key=f"radio_{i}",
                    label_visibility="collapsed",
                    disabled=submitted,
                )
                if selected:
                    st.session_state["quiz_answers"][answer_key] = selected

        elif q_type == "true_false":
            selected = st.radio(
                f"Select your answer for Q{q_num}",
                options=["True", "False"],
                key=f"radio_{i}",
                label_visibility="collapsed",
                disabled=submitted,
            )
            if selected:
                st.session_state["quiz_answers"][answer_key] = selected

        elif q_type == "short_answer":
            answer = st.text_input(
                f"Your answer for Q{q_num}",
                key=f"text_{i}",
                label_visibility="collapsed",
                disabled=submitted,
            )
            if answer:
                st.session_state["quiz_answers"][answer_key] = answer

        # Show feedback if submitted
        if submitted:
            correct = q.get("correct_answer", "")
            user_answer = st.session_state["quiz_answers"].get(answer_key, "")
            explanation = q.get("explanation", "")

            is_correct = _check_answer(q_type, user_answer, correct)

            if is_correct:
                st.success(f"✅ Correct! {explanation}")
            else:
                st.error(f"❌ Incorrect. The correct answer is: **{correct}**")
                if explanation:
                    st.info(f"💡 {explanation}")

        st.markdown("---")

    # Submit / New Quiz buttons
    if not submitted:
        if st.button("📝 Submit Quiz", use_container_width=True, type="primary"):
            st.session_state["quiz_submitted"] = True
            score = _calculate_score(questions, st.session_state["quiz_answers"])
            st.session_state["quiz_score"] = score
            st.rerun()
    else:
        # Show score summary
        score = st.session_state.get("quiz_score", {})
        correct = score.get("correct", 0)
        total = score.get("total", 0)
        percentage = score.get("percentage", 0)

        # Score display
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Score", f"{correct}/{total}")
        with col2:
            st.metric("Percentage", f"{percentage}%")
        with col3:
            grade = _get_grade(percentage)
            st.metric("Grade", grade)

        # Progress bar
        st.progress(percentage / 100)

        # Encouragement message
        if percentage >= 80:
            st.balloons()
            st.success("🎉 Excellent work! You've mastered this material!")
        elif percentage >= 60:
            st.success("👍 Good job! Keep reviewing to improve further.")
        elif percentage >= 40:
            st.warning("📚 You're getting there! Review the topics you missed.")
        else:
            st.warning("💪 Don't give up! Review your materials and try again.")

        # New quiz button
        if st.button(
            "🔄 Generate New Quiz", use_container_width=True, type="secondary"
        ):
            st.session_state.pop("quiz_questions", None)
            st.session_state.pop("quiz_answers", None)
            st.session_state.pop("quiz_submitted", None)
            st.session_state.pop("quiz_score", None)
            st.rerun()


def _check_answer(q_type: str, user_answer: str, correct_answer: str) -> bool:
    """Check if the user's answer matches the correct answer."""
    if not user_answer:
        return False

    if q_type == "mcq":
        # Compare the letter prefix (A, B, C, D)
        user_letter = user_answer.strip()[0].upper() if user_answer.strip() else ""
        correct_letter = correct_answer.strip()[0].upper() if correct_answer.strip() else ""
        return user_letter == correct_letter

    elif q_type == "true_false":
        return user_answer.strip().lower() == correct_answer.strip().lower()

    elif q_type == "short_answer":
        # Fuzzy match: check if the core of the correct answer is in the user's answer
        user_clean = user_answer.strip().lower()
        correct_clean = correct_answer.strip().lower()
        return correct_clean in user_clean or user_clean in correct_clean

    return False


def _calculate_score(questions: list, answers: dict) -> dict:
    """Calculate the quiz score."""
    total = len(questions)
    correct = 0

    for i, q in enumerate(questions):
        answer_key = f"q_{i}"
        user_answer = answers.get(answer_key, "")
        correct_answer = q.get("correct_answer", "")

        if _check_answer(q.get("type", ""), user_answer, correct_answer):
            correct += 1

    percentage = round((correct / total) * 100) if total > 0 else 0

    return {
        "correct": correct,
        "total": total,
        "percentage": percentage,
    }


def _get_grade(percentage: int) -> str:
    """Return a letter grade based on percentage."""
    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B"
    elif percentage >= 60:
        return "C"
    elif percentage >= 50:
        return "D"
    else:
        return "F"


def render_quiz_page() -> None:
    """Main entry point — renders quiz setup or active quiz."""
    if "quiz_questions" in st.session_state and st.session_state["quiz_questions"]:
        _render_quiz_questions()
    else:
        _render_quiz_setup()
