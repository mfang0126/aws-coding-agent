"""General utility functions."""

from typing import Any, Dict


def extract_text_from_event(event: Dict[str, Any]) -> str:
    """Extract text from Strands streaming event.

    Handles multiple event formats.

    Args:
        event: Streaming event dict

    Returns:
        Extracted text or empty string
    """
    # Event format 1: {"type": "text", "text": "..."}
    if event.get("type") == "text":
        return event.get("text", "")

    # Event format 2: {"content": [{"type": "text", "text": "..."}]}
    if "content" in event:
        for item in event["content"]:
            if item.get("type") == "text":
                return item.get("text", "")

    return ""


def log_server(msg: str, level: str = "info"):
    """Server-side logging (not sent to client).

    Args:
        msg: Log message
        level: "info", "success", "warning", "error"
    """
    emoji = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
    }
    print(f"{emoji.get(level, 'ℹ️')} [SERVER] {msg}")
