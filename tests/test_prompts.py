"""Tests for prompt templates."""
from src.constants.prompts import (
    CODING_AGENT_SYSTEM_PROMPT,
    PR_REVIEW_PLAN_PROMPT_TEMPLATE,
)
from src.constants.messages import generate_plan_markdown, generate_status_json


class TestSystemPrompts:
    """Tests for system prompts."""

    def test_coding_agent_prompt_exists(self):
        """Test that coding agent prompt is defined."""
        assert CODING_AGENT_SYSTEM_PROMPT is not None
        assert len(CODING_AGENT_SYSTEM_PROMPT) > 0
        assert "GitHub" in CODING_AGENT_SYSTEM_PROMPT

    def test_pr_review_prompt_template_exists(self):
        """Test that PR review template exists."""
        assert PR_REVIEW_PLAN_PROMPT_TEMPLATE is not None
        assert "{pr_number}" in PR_REVIEW_PLAN_PROMPT_TEMPLATE
        assert "{title}" in PR_REVIEW_PLAN_PROMPT_TEMPLATE


class TestTemplates:
    """Tests for template generation functions."""

    def test_generate_plan_markdown(self):
        """Test markdown plan generation."""
        markdown = generate_plan_markdown(
            objective="Test objective",
            steps=["Step 1", "Step 2", "Step 3"],
            risks=["Risk 1", "Risk 2"],
            time_min=10
        )

        assert "Test objective" in markdown
        assert "Step 1" in markdown
        assert "Step 2" in markdown
        assert "Step 3" in markdown
        assert "Risk 1" in markdown
        assert "Risk 2" in markdown
        assert "10 minutes" in markdown

    def test_generate_plan_markdown_empty_risks(self):
        """Test markdown generation with empty risks."""
        markdown = generate_plan_markdown(
            objective="Test",
            steps=["Step 1"],
            risks=[],
            time_min=5
        )

        assert "None identified" in markdown

    def test_generate_status_json(self):
        """Test JSON status generation."""
        status_dict = generate_status_json(
            status="in_progress",
            step="Current step",
            progress=75,
            issues=["Issue 1"]
        )

        assert status_dict["status"] == "in_progress"
        assert status_dict["current_step"] == "Current step"
        assert status_dict["progress"] == 75
        assert status_dict["issues"] == ["Issue 1"]
        assert "updated_at" in status_dict

    def test_generate_status_json_empty_issues(self):
        """Test status generation with empty issues."""
        status_dict = generate_status_json(
            status="completed",
            step="Done",
            progress=100,
            issues=[]
        )

        assert status_dict["issues"] == []
