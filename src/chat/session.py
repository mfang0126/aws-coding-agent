"""
Session management for chat conversations.
Pure functions for session state tracking.
"""
from datetime import datetime

from ..models.chat import ChatMessage


class SessionManager:
    """
    Simple session state manager.
    In production, this would use Redis or DynamoDB.
    """

    def __init__(self):
        self._sessions: dict[str, list[ChatMessage]] = {}

    def add_message(self, message: ChatMessage) -> None:
        """Add a message to session history."""
        if message.session_id not in self._sessions:
            self._sessions[message.session_id] = []

        self._sessions[message.session_id].append(message)

    def get_messages(self, session_id: str, limit: int | None = None) -> list[ChatMessage]:
        """Get message history for a session."""
        messages = self._sessions.get(session_id, [])
        if limit:
            return messages[-limit:]
        return messages

    def clear_session(self, session_id: str) -> None:
        """Clear a session's history."""
        if session_id in self._sessions:
            del self._sessions[session_id]

    def get_active_sessions(self) -> list[str]:
        """Get list of active session IDs."""
        return list(self._sessions.keys())
