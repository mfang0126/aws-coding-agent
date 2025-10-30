"""Tests for session management."""
from src.chat.session import SessionManager
from src.models.chat import ChatMessage


class TestSessionManager:
    """Tests for SessionManager class."""

    def test_add_message_creates_session(self):
        """Test that adding a message creates a new session."""
        manager = SessionManager()

        msg = ChatMessage(
            message="Hello",
            session_id="sess_1"
        )

        manager.add_message(msg)

        messages = manager.get_messages("sess_1")
        assert len(messages) == 1
        assert messages[0].message == "Hello"

    def test_add_multiple_messages_same_session(self):
        """Test adding multiple messages to same session."""
        manager = SessionManager()

        msg1 = ChatMessage(message="Message 1", session_id="sess_1")
        msg2 = ChatMessage(message="Message 2", session_id="sess_1")
        msg3 = ChatMessage(message="Message 3", session_id="sess_1")

        manager.add_message(msg1)
        manager.add_message(msg2)
        manager.add_message(msg3)

        messages = manager.get_messages("sess_1")
        assert len(messages) == 3
        assert messages[0].message == "Message 1"
        assert messages[1].message == "Message 2"
        assert messages[2].message == "Message 3"

    def test_get_messages_with_limit(self):
        """Test getting messages with limit."""
        manager = SessionManager()

        for i in range(10):
            msg = ChatMessage(message=f"Message {i}", session_id="sess_1")
            manager.add_message(msg)

        messages = manager.get_messages("sess_1", limit=3)
        assert len(messages) == 3
        # Should get last 3 messages
        assert messages[0].message == "Message 7"
        assert messages[1].message == "Message 8"
        assert messages[2].message == "Message 9"

    def test_get_messages_nonexistent_session(self):
        """Test getting messages for session that doesn't exist."""
        manager = SessionManager()

        messages = manager.get_messages("nonexistent")
        assert messages == []

    def test_clear_session(self):
        """Test clearing a session."""
        manager = SessionManager()

        msg = ChatMessage(message="Test", session_id="sess_1")
        manager.add_message(msg)

        assert len(manager.get_messages("sess_1")) == 1

        manager.clear_session("sess_1")

        assert len(manager.get_messages("sess_1")) == 0

    def test_get_active_sessions(self):
        """Test getting list of active sessions."""
        manager = SessionManager()

        msg1 = ChatMessage(message="Test", session_id="sess_1")
        msg2 = ChatMessage(message="Test", session_id="sess_2")
        msg3 = ChatMessage(message="Test", session_id="sess_3")

        manager.add_message(msg1)
        manager.add_message(msg2)
        manager.add_message(msg3)

        active = manager.get_active_sessions()
        assert len(active) == 3
        assert "sess_1" in active
        assert "sess_2" in active
        assert "sess_3" in active

    def test_multiple_sessions_independent(self):
        """Test that multiple sessions are independent."""
        manager = SessionManager()

        msg1 = ChatMessage(message="Session 1 message", session_id="sess_1")
        msg2 = ChatMessage(message="Session 2 message", session_id="sess_2")

        manager.add_message(msg1)
        manager.add_message(msg2)

        sess1_messages = manager.get_messages("sess_1")
        sess2_messages = manager.get_messages("sess_2")

        assert len(sess1_messages) == 1
        assert len(sess2_messages) == 1
        assert sess1_messages[0].message == "Session 1 message"
        assert sess2_messages[0].message == "Session 2 message"
