"""
app/pages/planner.py — AI Daily Study Planner page for StudyPal.
"""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from core.retrieval.planner import generate_study_plan


# Activity icons
_ACTIVITY_ICONS = {
    "Flashcards": "📇",
    "Quiz": "🧠",
    "Q&A Chat": "💬",
    "Review": "🔁",
}

_ACTIVITY_COLORS = {
    "Flashcards": "#1e2a6e",
    "Quiz": "#2a1e6e",
    "Q&A Chat": "#1e4d38",
    "Review": "#4d3a1e",
}


def _get_icon(activity: str) -> str:
    for key, icon in _ACTIVITY_ICONS.items():
        if key.lower() in activity.lower():
            return icon
    return "📚"


def _render_plan_setup() -> None:
    """Render the study planner configuration panel."""
    st.header("📅 Daily Study Planner")
    st.caption("Get an AI-generated personalized study schedule for your exam")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        exam_date = st.date_input(
            "🎯 Exam / Deadline Date",
            value=date.today() + timedelta(days=14),
            min_value=date.today() + timedelta(days=1),
            help="When is your exam or assignment due?",
        )
    with col2:
        hours_per_day = st.slider(
            "⏰ Study Hours Per Day",
            min_value=0.5,
            max_value=8.0,
            value=2.0,
            step=0.5,
            help="How many hours can you study each day?",
        )

    col3, col4 = st.columns(2)
    with col3:
        days_per_week = st.selectbox(
            "📆 Study Days Per Week",
            options=[3, 4, 5, 6, 7],
            index=2,
            help="How many days per week can you study?",
        )
    with col4:
        collection = st.session_state.get("active_collection", "studypal_default")
        days_left = (exam_date - date.today()).days
        st.metric("Days Until Exam", days_left)

    st.markdown("")

    if st.button("📅 Generate My Study Plan", use_container_width=True, type="primary"):
        with st.spinner("Building your personalized study plan…"):
            try:
                plan = generate_study_plan(
                    exam_date=exam_date,
                    collection_name=collection,
                    hours_per_day=hours_per_day,
                    days_per_week=days_per_week,
                )
            except ValueError as e:
                st.error(str(e))
                return
            except Exception as e:
                st.error(f"Failed to generate plan: {e}")
                return

        if not plan:
            st.warning("Could not generate a plan. Make sure you have documents uploaded and try again.")
            return

        st.session_state["study_plan"] = plan
        st.session_state["plan_exam_date"] = exam_date
        st.rerun()


def _render_plan() -> None:
    """Render the generated study plan."""
    plan = st.session_state["study_plan"]
    exam_date = st.session_state.get("plan_exam_date")

    st.header("📅 Your Study Plan")

    # Summary metrics
    total_days = len(plan)
    total_sessions = sum(len(d.get("sessions", [])) for d in plan)
    total_mins = sum(
        s.get("duration_min", 0)
        for d in plan for s in d.get("sessions", [])
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📆 Study Days", total_days)
    with col2:
        st.metric("📋 Sessions", total_sessions)
    with col3:
        st.metric("⏱️ Total Hours", f"{round(total_mins / 60, 1)}h")

    if exam_date:
        days_left = (exam_date - date.today()).days
        st.progress(
            max(0.0, min(1.0, 1 - days_left / max(days_left, 1))),
        )
        st.caption(f"📍 {days_left} days until exam — {exam_date.strftime('%B %d, %Y')}")

    st.markdown("---")

    # Day-by-day schedule
    for day_data in plan:
        day_num = day_data.get("day", "?")
        day_date = day_data.get("date", "")
        focus = day_data.get("focus", "")
        sessions = day_data.get("sessions", [])

        # Format the date nicely if possible
        try:
            from datetime import datetime
            parsed = datetime.strptime(day_date, "%Y-%m-%d")
            day_label = parsed.strftime("%A, %b %d")
        except Exception:
            day_label = day_date

        is_review = any("review" in s.get("activity", "").lower() for s in sessions)
        day_emoji = "🔁" if is_review else "📖"

        with st.expander(
            f"{day_emoji} **Day {day_num}** — {day_label} · {focus}",
            expanded=(day_num <= 3),
        ):
            for session in sessions:
                activity = session.get("activity", "Study")
                topic = session.get("topic", "")
                duration = session.get("duration_min", 30)
                notes = session.get("notes", "")
                icon = _get_icon(activity)

                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**{icon} {activity}** — {topic}")
                    if notes:
                        st.caption(f"💡 {notes}")
                with col_b:
                    st.caption(f"⏱️ {duration} min")

                st.markdown("")

    st.markdown("---")

    # Download as markdown
    plan_md = _plan_to_markdown(plan, exam_date)
    col_dl, col_new = st.columns(2)
    with col_dl:
        st.download_button(
            label="⬇️ Download Plan (.md)",
            data=plan_md,
            file_name="studypal_study_plan.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_new:
        if st.button("🔄 Generate New Plan", use_container_width=True, type="secondary"):
            st.session_state.pop("study_plan", None)
            st.session_state.pop("plan_exam_date", None)
            st.rerun()


def _plan_to_markdown(plan: list, exam_date) -> str:
    """Convert the plan to a downloadable markdown file."""
    lines = [
        "# 📅 StudyPal — My Study Plan",
        "",
        f"**Exam Date:** {exam_date.strftime('%B %d, %Y') if exam_date else 'N/A'}",
        f"**Generated:** {date.today().strftime('%B %d, %Y')}",
        "",
        "---",
        "",
    ]
    for day_data in plan:
        day_num = day_data.get("day", "?")
        day_date = day_data.get("date", "")
        focus = day_data.get("focus", "")
        lines.append(f"## Day {day_num} — {day_date}: {focus}")
        for s in day_data.get("sessions", []):
            icon = _get_icon(s.get("activity", ""))
            lines.append(
                f"- {icon} **{s.get('activity', '')}** — {s.get('topic', '')} "
                f"({s.get('duration_min', 0)} min)"
            )
            if s.get("notes"):
                lines.append(f"  - 💡 {s['notes']}")
        lines.append("")
    return "\n".join(lines)


def render_planner_page() -> None:
    """Main entry point — renders setup or active plan."""
    if "study_plan" in st.session_state and st.session_state["study_plan"]:
        _render_plan()
    else:
        _render_plan_setup()
