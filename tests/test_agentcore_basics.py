"""AgentCore integration configuration and setup tests."""
import os
import pytest
from pydantic import ValidationError

from src.config import Settings
from src.models.plan import PlanModel
from src.models.chat import ChatMessage
from src.models.status import StatusModel


class TestAgentCoreConfiguration:
    """Tests for AgentCore environment and configuration setup."""

    def test_agentcore_required_environment_variables(self):
        """Test that AgentCore requires specific environment variables."""
        # AgentCore requires GitHub OAuth provider setup
        settings = Settings(
            github_client_id="test_client_id",
            github_client_secret="test_client_secret"
        )

        # Verify AgentCore defaults
        assert settings.aws_region == "ap-southeast-2"
        # Check that model_id contains claude-sonnet (actual value may vary)
        assert "claude-sonnet" in settings.model_id.lower()
        assert settings.github_provider_name == "github-provider"

    def test_agentcore_aws_configuration(self):
        """Test AWS configuration for AgentCore deployment."""
        settings = Settings(
            github_client_id="test_client_id",
            github_client_secret="test_client_secret",
            aws_region="us-east-1",
            model_id="anthropic.claude-sonnet-4.5"
        )

        # AgentCore deployment uses these AWS settings
        assert settings.aws_region == "us-east-1"
        assert settings.model_id == "anthropic.claude-sonnet-4.5"

    def test_agentcore_deployment_settings(self):
        """Test deployment-specific configuration for AgentCore."""
        settings = Settings(
            github_client_id="test_client_id",
            github_client_secret="test_client_secret",
            log_level="DEBUG"
        )

        # AgentCore debugging and monitoring
        assert settings.log_level == "DEBUG"
        assert settings.github_provider_name == "github-provider"

    def test_agentcore_secrets_management(self):
        """Test secret handling for AgentCore OAuth provider."""
        settings = Settings(
            github_client_id="secret_id",
            github_client_secret="secret_value"
        )

        # Verify secrets are protected in AgentCore deployment
        settings_str = str(settings)
        assert "secret_id" not in settings_str
        assert "secret_value" not in settings_str


class TestAgentCoreDataModels:
    """Tests for data models used by AgentCore runtime."""

    def test_plan_model_for_agentcore_tasks(self):
        """Test PlanModel structure for AgentCore task execution."""
        plan = PlanModel(
            objective="Review PR for security issues",
            steps=["Fetch PR from GitHub", "Analyze code changes", "Generate review comments"],
            risks=["Large PR may timeout in AgentCore"],
            estimated_time_minutes=15
        )

        # AgentCore runtime expects these fields
        assert plan.objective == "Review PR for security issues"
        assert len(plan.steps) == 3
        assert plan.estimated_time_minutes == 15
        assert plan.risks == ["Large PR may timeout in AgentCore"]

    def test_chat_message_format_for_agentcore(self):
        """Test ChatMessage format expected by AgentCore conversations."""
        message = ChatMessage(
            message="Please review this pull request",
            session_id="agentcore_session_123"
        )

        # AgentCore conversation format
        assert message.message == "Please review this pull request"
        assert message.session_id == "agentcore_session_123"

    def test_status_model_for_agentcore_monitoring(self):
        """Test StatusModel for AgentCore execution status."""
        status = StatusModel(
            status="in_progress",
            current_step="Analyzing PR with AgentCore",
            progress=60
        )

        # AgentCore monitoring expects this format
        assert status.status == "in_progress"
        assert "AgentCore" in status.current_step
        assert status.progress == 60

    def test_agentcore_model_validation(self):
        """Test that models validate AgentCore-required fields."""
        # PlanModel requires objective
        with pytest.raises(ValidationError):
            PlanModel(
                steps=["Step 1"],
                estimated_time_minutes=10
            )

        # ChatMessage requires message
        with pytest.raises(ValidationError):
            ChatMessage(message=None, session_id="test")

        # StatusModel requires status and current_step
        with pytest.raises(ValidationError):
            StatusModel(status="test", current_step=None)

    def test_agentcore_model_defaults(self):
        """Test model defaults that work with AgentCore."""
        plan = PlanModel(
            objective="Test objective",
            steps=["Step 1"],
            estimated_time_minutes=5
        )

        # Defaults should be compatible with AgentCore
        assert plan.risks == []  # Empty list is valid for AgentCore