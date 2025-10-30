"""Tests for data models."""
from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models.chat import ChatMessage
from src.models.plan import PlanModel
from src.models.status import StatusModel


class TestPlanModel:
    """Tests for PlanModel."""

    def test_plan_model_valid(self):
        """Test creating valid plan model."""
        plan = PlanModel(
            objective="Review PR for security issues",
            steps=["Fetch PR", "Analyze code", "Post comments"],
            risks=["Large PR may take time"],
            estimated_time_minutes=15
        )

        assert plan.objective == "Review PR for security issues"
        assert len(plan.steps) == 3
        assert len(plan.risks) == 1
        assert plan.estimated_time_minutes == 15

    def test_plan_model_requires_objective(self):
        """Test that objective is required."""
        with pytest.raises(ValidationError):
            PlanModel(
                steps=["Step 1"],
                estimated_time_minutes=10
            )

    def test_plan_model_default_risks_empty(self):
        """Test that risks defaults to empty list."""
        plan = PlanModel(
            objective="Test objective",
            steps=["Step 1"],
            estimated_time_minutes=5
        )

        assert plan.risks == []


class TestStatusModel:
    """Tests for StatusModel."""

    def test_status_model_valid(self):
        """Test creating valid status model."""
        status = StatusModel(
            status="in_progress",
            current_step="Analyzing code",
            progress=50,
            issues=[]
        )

        assert status.status == "in_progress"
        assert status.current_step == "Analyzing code"
        assert status.progress == 50
        assert isinstance(status.updated_at, datetime)

    def test_status_model_validates_progress_range(self):
        """Test that progress is validated to 0-100 range."""
        with pytest.raises(ValidationError):
            StatusModel(
                status="in_progress",
                current_step="Step",
                progress=150,  # Invalid
                issues=[]
            )

        with pytest.raises(ValidationError):
            StatusModel(
                status="in_progress",
                current_step="Step",
                progress=-10,  # Invalid
                issues=[]
            )

    def test_status_model_default_issues_empty(self):
        """Test that issues defaults to empty list."""
        status = StatusModel(
            status="completed",
            current_step="Done",
            progress=100
        )

        assert status.issues == []


class TestChatMessage:
    """Tests for ChatMessage."""

    def test_chat_message_valid(self):
        """Test creating valid chat message."""
        msg = ChatMessage(
            message="Hello, agent!",
            session_id="sess_123",
            user_id="user_456"
        )

        assert msg.message == "Hello, agent!"
        assert msg.session_id == "sess_123"
        assert msg.user_id == "user_456"
        assert isinstance(msg.timestamp, datetime)

    def test_chat_message_user_id_optional(self):
        """Test that user_id is optional."""
        msg = ChatMessage(
            message="Test message",
            session_id="sess_789"
        )

        assert msg.user_id is None

    def test_chat_message_metadata_optional(self):
        """Test that metadata is optional."""
        msg = ChatMessage(
            message="Test",
            session_id="sess_abc"
        )

        assert msg.metadata is None

    def test_chat_message_with_metadata(self):
        """Test chat message with metadata."""
        msg = ChatMessage(
            message="Review PR #123",
            session_id="sess_xyz",
            metadata={"intent": "pr_review", "pr_number": 123}
        )

        assert msg.metadata["intent"] == "pr_review"
        assert msg.metadata["pr_number"] == 123
