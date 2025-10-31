"""
Configuration management using Pydantic Settings.
Loads from environment variables with validation.
"""
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses Pydantic validation and SecretStr for sensitive data.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # AWS Configuration
    aws_region: str = Field(default="ap-southeast-2", description="AWS region")
    aws_profile: str | None = Field(default=None, description="AWS CLI profile name")

    # GitHub OAuth (optional - not needed when using AgentCore OAuth providers)
    github_client_id: SecretStr | None = Field(default=None, description="GitHub OAuth App Client ID")
    github_client_secret: SecretStr | None = Field(default=None, description="GitHub OAuth App Client Secret")

    # GitHub Personal Access Token (optional, for local dev)
    github_token: SecretStr | None = Field(
        default=None,
        description="GitHub Personal Access Token for local development (bypasses OAuth)"
    )

    # Agent Configuration
    model_id: str = Field(
        default="anthropic.claude-sonnet-4.5",
        description="Bedrock model ID"
    )
    log_level: str = Field(default="INFO", description="Logging level")

    # OAuth Provider Configuration
    github_provider_name: str = Field(
        default="github-provider",
        description="OAuth2 credential provider name"
    )
    oauth_workload_name: str = Field(
        default="coding-agent-workload",
        description="OAuth workload name"
    )


# Global settings instance - lazy loaded to avoid requiring env vars at import time
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# For backward compatibility, try to create settings but don't fail if env vars missing
try:
    settings = Settings()
except Exception:
    # Settings will be created lazily when needed
    settings = None  # type: ignore
