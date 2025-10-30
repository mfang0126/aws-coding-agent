"""
Streaming chat API - functional endpoints, minimal state.
"""
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .agent.create_agent import create_coding_agent
from .chat.stream_handler import stream_agent_response
from .config import settings, get_settings
from .utils.logging import get_logger, setup_logging

# Get settings, using default log level if not configured
try:
    app_settings = get_settings() if settings is None else settings
    setup_logging(app_settings.log_level)
except Exception:
    # Fallback if settings can't be loaded (no .env file)
    setup_logging("INFO")

logger = get_logger(__name__)

app = FastAPI(
    title="Coding Agent Chat",
    version="1.0.0",
    description="AI coding assistant with GitHub OAuth and PR review automation"
)

# Single agent instance (persists in container)
# Only create if settings are properly configured
try:
    agent = create_coding_agent()
    logger.info("agent_created", status="success")
except Exception as e:
    logger.warning("agent_creation_skipped", reason=str(e))
    agent = None


class ChatRequest(BaseModel):
    """Chat message from user."""
    message: str
    session_id: str


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint using Server-Sent Events.
    Agent autonomously decides when to use GitHub tools.

    Args:
        request: Chat request with message and session_id

    Returns:
        StreamingResponse with SSE events
    """
    if agent is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Agent not configured. Please set up .env file with required credentials."
        )

    logger.info("chat_request", session_id=request.session_id)

    return StreamingResponse(
        stream_agent_response(agent, request.message, request.session_id),
        media_type="text/event-stream"
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "coding-agent",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
