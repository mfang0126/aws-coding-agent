"""Plan data model for PR review planning."""
from pydantic import BaseModel, Field


class PlanModel(BaseModel):
    """
    Structured plan for PR review workflow.
    Agent generates this before executing review steps.
    """

    objective: str = Field(..., description="What the review aims to achieve")
    steps: list[str] = Field(..., description="Sequential steps to execute")
    risks: list[str] = Field(default_factory=list, description="Potential issues to watch for")
    estimated_time_minutes: int = Field(..., description="Estimated completion time in minutes")

    model_config = {
        "json_schema_extra": {
            "example": {
                "objective": "Review PR #42 for security and code quality issues",
                "steps": [
                    "Fetch PR details and changed files",
                    "Analyze authentication changes in auth.py",
                    "Check for SQL injection vulnerabilities",
                    "Review test coverage",
                    "Post review comments"
                ],
                "risks": [
                    "Large PR (200+ lines) may require extended analysis",
                    "Database schema changes need migration validation"
                ],
                "estimated_time_minutes": 15
            }
        }
    }
