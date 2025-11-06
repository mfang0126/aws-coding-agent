"""Standardized messages and response templates."""
from datetime import datetime


# Success messages
SUCCESS_CREATED = "✅ Created {resource}: {name}\nURL: {url}"
SUCCESS_UPDATED = "✅ Updated {resource}: {name}"
SUCCESS_DELETED = "✅ Deleted {resource}: {name}"
SUCCESS_OPERATION = "✅ Operation completed: {details}"

# Error messages
ERROR_AUTH_REQUIRED = "❌ Authentication required. Please authorize the app."
ERROR_NOT_FOUND = "❌ Resource not found: {resource}"
ERROR_PERMISSION_DENIED = "❌ Permission denied. Check OAuth scopes."
ERROR_API_ERROR = "❌ API error ({status}): {message}"
ERROR_NETWORK_ERROR = "❌ Network error: {message}"

# Info messages
INFO_INITIALIZING = "🔐 Initializing authentication..."
INFO_AUTHENTICATED = "✅ Authentication successful"
INFO_PROCESSING = "🚀 Processing request..."

# OAuth messages
OAUTH_REQUIRED_TEMPLATE = """🔐 Authorization Required

Please authorize the app:
{oauth_url}

After authorizing, try your request again.
"""


# Template generation functions - pure, no state
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
