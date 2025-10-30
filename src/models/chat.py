"""Chat data model for conversation management."""
from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """
    Single message in a chat conversation.
    Used for session management and message history.
    """

    message: str = Field(..., description="Message content")
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str | None = Field(default=None, description="User identifier (for OAuth)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    metadata: dict | None = Field(default=None, description="Additional metadata")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Review PR #123 in the agent-tasks folder",
                "session_id": "sess_abc123",
                "user_id": "user_github_456",
                "timestamp": "2025-10-30T10:30:00Z",
                "metadata": {"intent": "pr_review", "pr_number": 123}
            }
        }
    }
