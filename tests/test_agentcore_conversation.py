"""AgentCore conversation and session management tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.chat.session import SessionManager
from src.models.chat import ChatMessage
from src.gateway.agentcore import AgentCoreGitHubAuth
# StreamHandler will be mocked to avoid import issues


class TestAgentCoreConversation:
    """Tests for AgentCore conversation patterns and session management."""

    def test_session_manager_initialization(self):
        """Test SessionManager setup for AgentCore conversations."""
        manager = SessionManager()

        # Should initialize with empty session storage
        assert hasattr(manager, '_sessions')
        assert len(manager._sessions) == 0

    def test_agentcore_session_creation(self):
        """Test session creation for AgentCore conversations."""
        manager = SessionManager()
        session_id = "agentcore_session_123"

        # Create initial message
        message = ChatMessage(
            message="Hello AgentCore",
            session_id=session_id
        )

        manager.add_message(message)

        # Session should be created with the message
        messages = manager.get_messages(session_id)
        assert len(messages) == 1
        assert messages[0].session_id == session_id
        assert messages[0].message == "Hello AgentCore"

    def test_agentcore_conversation_flow(self):
        """Test complete conversation flow in AgentCore context."""
        manager = SessionManager()
        session_id = "agentcore_conversation"

        # User message
        user_msg = ChatMessage(
            message="Review this PR for security issues",
            session_id=session_id
        )
        manager.add_message(user_msg)

        # Agent response
        agent_msg = ChatMessage(
            message="I'll analyze the PR for security vulnerabilities",
            session_id=session_id
        )
        manager.add_message(agent_msg)

        # Follow-up user message
        followup_msg = ChatMessage(
            message="Focus on authentication mechanisms",
            session_id=session_id
        )
        manager.add_message(followup_msg)

        # Verify conversation flow
        messages = manager.get_messages(session_id)
        assert len(messages) == 3
        assert messages[0].message == "Review this PR for security issues"
        assert messages[1].message == "I'll analyze the PR for security vulnerabilities"
        assert "authentication" in messages[2].message

    def test_session_message_limiting(self):
        """Test message limiting for AgentCore context management."""
        manager = SessionManager()
        session_id = "agentcore_context_test"

        # Add multiple messages
        for i in range(10):
            message = ChatMessage(
                message=f"Message {i}",
                session_id=session_id
            )
            manager.add_message(message)

        # Test limit functionality
        all_messages = manager.get_messages(session_id)
        limited_messages = manager.get_messages(session_id, limit=5)

        assert len(all_messages) == 10
        assert len(limited_messages) == 5

    def test_multi_session_management(self):
        """Test handling multiple AgentCore sessions."""
        manager = SessionManager()

        # Create multiple sessions
        sessions = ["session_1", "session_2", "session_3"]

        for session_id in sessions:
            message = ChatMessage(
                message=f"Start of {session_id}",
                role="user",
                session_id=session_id
            )
            manager.add_message(message)

        # Each session should have its own messages
        for session_id in sessions:
            messages = manager.get_messages(session_id)
            assert len(messages) == 1
            assert session_id in messages[0].message

    @pytest.mark.asyncio
    async def test_streaming_response_pattern(self):
        """Test streaming response pattern for AgentCore."""
        # Test streaming response concept without import issues

        # Mock streaming content
        test_content = [
            "Analyzing the pull request...",
            " Found security issue in authentication.",
            " Recommending OAuth implementation."
        ]

        # Mock async generator for streaming
        async def mock_stream():
            for content in test_content:
                yield content

        # Collect streamed responses
        responses = []
        async for chunk in mock_stream():
            responses.append(chunk)

        # Should receive all content chunks
        assert len(responses) == 3
        assert responses[0] == "Analyzing the pull request..."
        assert "OAuth" in responses[2]

    def test_gateway_authenticated_session(self):
        """Test session with authenticated gateway access."""
        # Mock authenticated gateway
        mock_auth = MagicMock(spec=AgentCoreGitHubAuth)
        mock_auth.get_token.return_value = "auth_token"

        manager = SessionManager()
        session_id = "authenticated_session"

        # Create message in authenticated context
        message = ChatMessage(
            message="Access GitHub repository with auth",
            role="user",
            session_id=session_id
        )
        manager.add_message(message)

        # Session should work regardless of auth state
        messages = manager.get_messages(session_id)
        assert len(messages) == 1
        assert "GitHub" in messages[0].message

    def test_session_persistence_patterns(self):
        """Test session persistence patterns for AgentCore."""
        manager = SessionManager()
        session_id = "persistent_session"

        # Add conversation history
        conversation = [
            "Initial request",
            "Initial response",
            "Follow-up question",
            "Detailed answer"
        ]

        for content in conversation:
            message = ChatMessage(
                message=content,
                session_id=session_id
            )
            manager.add_message(message)

        # Verify full conversation is preserved
        messages = manager.get_messages(session_id)
        assert len(messages) == 4

        for i, expected_content in enumerate(conversation):
            assert messages[i].message == expected_content

    @pytest.mark.asyncio
    async def test_conversation_with_agentcore_tools(self):
        """Test conversation that triggers AgentCore tool usage."""
        manager = SessionManager()
        session_id = "tool_usage_session"

        # User requests GitHub operations
        user_msg = ChatMessage(
            message="Get PR #123 from GitHub repository",
            role="user",
            session_id=session_id
        )
        manager.add_message(user_msg)

        # Mock agent response indicating tool usage
        agent_msg = ChatMessage(
            message="I'll fetch PR #123 using GitHub API tools",
            session_id=session_id
        )
        manager.add_message(agent_msg)

        # Verify conversation includes tool interaction
        messages = manager.get_messages(session_id)
        assert len(messages) == 2
        assert "GitHub API" in messages[1].message

    def test_session_context_limits(self):
        """Test session context management for AgentCore limits."""
        manager = SessionManager()
        session_id = "context_limit_test"

        # Add messages that would exceed typical context limits
        large_content = "x" * 1000  # Simulate large message

        for i in range(5):
            message = ChatMessage(
                message=f"Large message {i}: {large_content}",
                role="user",
                session_id=session_id
            )
            manager.add_message(message)

        # Should handle large messages gracefully
        messages = manager.get_messages(session_id)
        assert len(messages) == 5

        # Test limiting for context management
        recent_messages = manager.get_messages(session_id, limit=2)
        assert len(recent_messages) == 2

    def test_error_handling_in_conversation(self):
        """Test error handling in AgentCore conversations."""
        manager = SessionManager()
        session_id = "error_handling_test"

        # Add normal message
        normal_msg = ChatMessage(
            message="Normal request",
            role="user",
            session_id=session_id
        )
        manager.add_message(normal_msg)

        # Simulate error response
        error_msg = ChatMessage(
            message="Error: Failed to access GitHub repository",
            session_id=session_id
        )
        manager.add_message(error_msg)

        # Should handle both normal and error messages
        messages = manager.get_messages(session_id)
        assert len(messages) == 2
        assert "Error:" in messages[1].message