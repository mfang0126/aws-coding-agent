"""
AgentCore Runtime entrypoint.
This module is referenced in .bedrock_agentcore.yaml for deployment.
"""
from .create_agent import create_coding_agent

# AgentCore expects an 'agent' variable at module level
agent = create_coding_agent()
