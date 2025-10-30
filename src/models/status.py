"""Status data model for progress tracking."""
from datetime import datetime

from pydantic import BaseModel, Field


class StatusModel(BaseModel):
    """
    Progress status for ongoing operations.
    Used to track PR review progress and report to user.
    """

    status: str = Field(..., description="Current status: pending, in_progress, completed, failed")
    current_step: str = Field(..., description="Description of current step")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    issues: list[str] = Field(default_factory=list, description="Any issues encountered")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "in_progress",
                "current_step": "Analyzing authentication changes",
                "progress": 60,
                "issues": [],
                "updated_at": "2025-10-30T10:30:00Z"
            }
        }
    }
