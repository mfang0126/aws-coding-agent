"""Tests for configuration module."""
import pytest
from pydantic import ValidationError

from src.config import Settings


def test_settings_loads_defaults():
    """Test that settings loads with defaults when env vars missing."""
    # This will use defaults for optional fields
    # Required fields (github_client_id/secret) need env vars or will fail
    settings = Settings(
        github_client_id="test_client_id",
        github_client_secret="test_client_secret"
    )

    assert settings.aws_region == "ap-southeast-2"
    assert settings.model_id == "anthropic.claude-sonnet-4.5"
    assert settings.log_level == "INFO"
    assert settings.github_provider_name == "github-provider"


def test_settings_validates_required_fields():
    """Test that required fields raise validation errors."""
    with pytest.raises(ValidationError) as exc_info:
        Settings()

    errors = exc_info.value.errors()
    error_fields = {error['loc'][0] for error in errors}
    assert 'github_client_id' in error_fields
    assert 'github_client_secret' in error_fields


def test_settings_uses_custom_values():
    """Test that custom values override defaults."""
    settings = Settings(
        github_client_id="custom_id",
        github_client_secret="custom_secret",
        aws_region="us-east-1",
        model_id="custom-model",
        log_level="DEBUG"
    )

    assert settings.aws_region == "us-east-1"
    assert settings.model_id == "custom-model"
    assert settings.log_level == "DEBUG"
    assert settings.github_client_id.get_secret_value() == "custom_id"


def test_settings_secrets_protected():
    """Test that secret values are protected."""
    settings = Settings(
        github_client_id="secret_id",
        github_client_secret="secret_value"
    )

    # Secrets should not be in string representation
    settings_str = str(settings)
    assert "secret_id" not in settings_str
    assert "secret_value" not in settings_str

    # But can be accessed with get_secret_value()
    assert settings.github_client_id.get_secret_value() == "secret_id"
    assert settings.github_client_secret.get_secret_value() == "secret_value"
