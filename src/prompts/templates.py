"""Template generation functions - pure, no state."""
from datetime import datetime


def generate_plan_markdown(
    objective: str,
    steps: list[str],
    risks: list[str],
    time_min: int
) -> str:
    """Generate PR plan as GitHub-flavored markdown."""
    steps_md = "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))
    risks_md = "\n".join(f"- {r}" for r in risks) if risks else "None identified"

    return f"""## 🤖 Proposed Review Plan

**Objective:** {objective}

**Steps:**
{steps_md}

**Potential Risks:**
{risks_md}

**Estimated Time:** {time_min} minutes

---
Reply with `approve` to proceed or `cancel` to abort.
"""


def generate_status_json(
    status: str,
    step: str,
    progress: int,
    issues: list[str]
) -> dict:
    """Generate status object - returns dict for JSON serialization."""
    return {
        "status": status,
        "current_step": step,
        "progress": progress,
        "issues": issues,
        "updated_at": datetime.utcnow().isoformat()
    }
