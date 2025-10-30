"""
Streaming chat logic using Server-Sent Events (SSE).
Pure async functions - no class needed.
"""
import asyncio
import json
from collections.abc import AsyncIterator

import structlog
from strands import Agent

from ..models.chat import ChatMessage

logger = structlog.get_logger()


async def stream_agent_response(
    agent: Agent,
    message: str,
    session_id: str
) -> AsyncIterator[str]:
    """
    Stream agent responses as SSE events.
    Yields JSON strings for SSE transmission.

    Args:
        agent: Strands Agent instance
        message: User message
        session_id: Session identifier

    Yields:
        SSE-formatted JSON strings
    """
    logger.info("streaming_response", session_id=session_id)

    try:
        # Strands async streaming (yields events in real-time)
        async for event in agent.stream_async(message, invocation_state={"session_id": session_id}):
            # Events are dictionaries from Strands SDK
            if not isinstance(event, dict):
                continue

            # Text token chunks
            if 'data' in event:
                yield f"data: {json.dumps({'type': 'token', 'content': event['data']})}\n\n"

            # Tool usage events
            elif 'current_tool_use' in event:
                tool_use = event['current_tool_use']
                tool_info = {
                    'type': 'tool_use',
                    'tool_name': tool_use.get('name'),
                    'tool_input': tool_use.get('input')
                }
                yield f"data: {json.dumps(tool_info)}\n\n"

            # Error events
            elif 'error' in event:
                yield f"data: {json.dumps({'type': 'error', 'message': str(event['error'])})}\n\n"
                break

        # Stream complete
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        logger.error("streaming_failed", error=str(e))
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


async def handle_pr_review_intent(
    agent: Agent,
    pr_number: int,
    session_id: str
) -> AsyncIterator[str]:
    """
    Special handler when user intent is PR review.
    Still streams but follows structured workflow.

    Args:
        agent: Strands Agent instance
        pr_number: PR number to review
        session_id: Session identifier

    Yields:
        SSE-formatted JSON strings
    """
    from ..prompts.system_prompts import PR_REVIEW_PLAN_PROMPT_TEMPLATE
    from ..prompts.templates import generate_plan_markdown

    # Step 1: Fetch PR via GitHub tools (agent does this autonomously)
    plan_prompt = f"Create a review plan for PR #{pr_number} in /agent-tasks/ folder"

    # Agent streams plan generation
    async for chunk in stream_agent_response(agent, plan_prompt, session_id):
        yield chunk

    # Wait for user approval (in real chat, they'll reply)
    # This is handled by chat session state in production
