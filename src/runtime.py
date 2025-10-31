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
# HTTP protocol requires specific port configuration
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
    # HTTP protocol requires port 8080 for AgentCore
    # See: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-http-protocol-contract.html
    import os
    # Force port 8080 regardless of how module is invoked
    os.environ.setdefault("BEDROCK_AGENTCORE_PORT", "8080")
    app.run(port=8080, host="0.0.0.0")

# Module-level invocation (python -m src.runtime)
# This ensures port 8080 is used when run as module
import sys
if "runpy" in sys.modules and not hasattr(sys, "_called_from_test"):
    import os
    os.environ.setdefault("BEDROCK_AGENTCORE_PORT", "8080")
    app.run(port=8080, host="0.0.0.0")
