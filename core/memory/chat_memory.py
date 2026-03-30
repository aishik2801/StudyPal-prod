"""
Chat memory — session-isolated in-memory chat history using langchain_core.
"""

from __future__ import annotations

from langchain_core.chat_history import InMemoryChatMessageHistory

# In-process cache keyed by session id
_HISTORY_STORE: dict[str, InMemoryChatMessageHistory] = {}


def get_chat_memory(session_id: str = "default") -> InMemoryChatMessageHistory:
    """
    Return an InMemoryChatMessageHistory for the given session.
    Creates a new one if it doesn't exist yet.
    """
    if session_id not in _HISTORY_STORE:
        _HISTORY_STORE[session_id] = InMemoryChatMessageHistory()
    return _HISTORY_STORE[session_id]


def clear_chat_memory(session_id: str = "default") -> None:
    """Wipe chat memory for a session."""
    if session_id in _HISTORY_STORE:
        _HISTORY_STORE[session_id].clear()


def clear_all_memory() -> None:
    """Wipe chat memory for every session."""
    for history in _HISTORY_STORE.values():
        history.clear()
    _HISTORY_STORE.clear()
