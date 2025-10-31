"""
AgentCore Runtime Wrapper (Optional)

This module provides AWS BedrockAgentCore integration for the coding agent.
It's OPTIONAL - the agent works fine without it in containers (ECS, K8s, etc).

Use this for:
- AWS AgentCore deployments
- Built-in AWS Identity/OAuth integration
- AgentCore memory features
- AWS-native monitoring

For 3rd party containers, use src/main.py (FastAPI) instead.
"""
from typing import AsyncIterator, Dict, Any
from bedrock_agentcore.runtime import BedrockAgentCoreApp

from src.agent.create_agent import create_coding_agent

# Create AgentCore app wrapper
app = BedrockAgentCoreApp()

# Agent instance - created lazily on first request
_agent = None


def get_agent():
    """Get or create the agent instance (lazy loading)."""
    global _agent
    if _agent is None:
        _agent = create_coding_agent()
    return _agent


@app.entrypoint
async def invoke(payload: Dict[str, Any]):
    """
    AgentCore entrypoint for the coding agent.

    This wraps our pure Strands agent for AWS AgentCore integration.
    The agent itself remains container-agnostic.

    Args:
        payload: Request payload from AgentCore with 'prompt' key

    Yields:
        Streaming text responses
    """
    try:
        # Extract user input from payload
        user_input = payload.get("prompt", "")

        if not user_input:
            yield "Error: No prompt provided"
            return

        # Get agent instance (lazy loading)
        agent = get_agent()

        # Stream agent responses
        async for event in agent.stream_async(user_input):
            # Handle different event types from Strands
            if isinstance(event, dict):
                # Extract text from structured events
                if "content" in event:
                    yield str(event["content"])
                elif "text" in event:
                    yield str(event["text"])
                elif "message" in event:
                    yield str(event["message"])
            elif isinstance(event, str):
                yield event
            else:
                # For other types, convert to string
                yield str(event)

    except Exception as e:
        yield f"Error processing request: {str(e)}"


if __name__ == "__main__":
    app.run()
