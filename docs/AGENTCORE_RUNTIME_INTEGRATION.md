# AgentCore Runtime Integration

Technical overview of how BedrockAgentCore runtime integration works with Strands agents.

## Runtime Wrapper Architecture

### Core Components

```python
# src/runtime.py - Main entrypoint
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from src.agent.create_agent import create_coding_agent

app = BedrockAgentCoreApp()  # AgentCore wrapper
_agent = None  # Lazy-loaded agent instance

@app.entrypoint
async def invoke(payload: Dict[str, Any]):
    """AgentCore entrypoint for the coding agent."""
```

### Key Design Patterns

#### 1. Lazy Agent Loading
```python
def get_agent():
    """Get or create the agent instance (lazy loading)."""
    global _agent
    if _agent is None:
        _agent = create_coding_agent()
    return _agent
```

**Why this matters**: AgentCore creates multiple instances for scalability. Lazy loading prevents resource waste during cold starts and ensures each request gets its own properly configured agent.

#### 2. Streaming Response Pattern
```python
@app.entrypoint
async def invoke(payload: Dict[str, Any]):
    agent = get_agent()
    async for chunk in agent(payload["prompt"]):
        yield chunk
```

**AgentCore expects**: Async generators that yield response chunks. This pattern enables real-time streaming for better user experience.

#### 3. Payload Structure
```python
# Expected input from AgentCore
payload = {
    "prompt": "User request text",
    "session_id": "optional_session_identifier",
    "other_metadata": "additional_context"
}
```

**Requirements**: Must contain at least `prompt` key. Session_id enables conversation continuity.

## Configuration Requirements

### Runtime Configuration
```yaml
# .bedrock_agentcore.yaml
entrypoint: src/runtime.py
name: coding_agent
region: ap-southeast-2
runtime: python3.11
```

### Application Configuration
```python
# src/config.py - AgentCore-specific settings
class Settings(BaseSettings):
    github_provider_name: str = "github-provider"
    aws_region: str = "ap-southeast-2"
    model_id: str = "anthropic.claude-sonnet-4.5"
```

## Deployment Architecture

### Container Structure
```
Container Runtime:
├── BedrockAgentCoreApp (HTTP layer)
│   ├── /health - Health checks
│   ├── /ping - AWS protocol compliance
│   └── /invoke - Agent entrypoint
├── src/runtime.py (Application layer)
│   ├── Payload parsing
│   ├── Agent creation
│   └── Response streaming
└── Strands Agent (Logic layer)
    ├── Tool orchestration
    ├── GitHub integration
    └── Response generation
```

### Protocol Flow
1. **Request**: AWS AgentCore → HTTP POST to /invoke
2. **Parsing**: runtime.py extracts prompt from payload
3. **Processing**: Strands agent handles business logic
4. **Streaming**: Async generator yields response chunks
5. **Response**: AgentCore forwards chunks to user

## Error Handling Patterns

### Runtime Errors
```python
@app.entrypoint
async def invoke(payload: Dict[str, Any]):
    try:
        agent = get_agent()
        async for chunk in agent(payload["prompt"]):
            yield chunk
    except Exception as e:
        yield f"Error: {str(e)}"
```

### Health Checks
```python
@app.health
async def health_check():
    """Health check endpoint for AgentCore."""
    return {"status": "healthy", "agent": "coding_agent"}
```

## Performance Considerations

### Cold Start Optimization
- Lazy agent creation reduces startup time
- Global agent instance reuse within same container
- Efficient credential caching

### Memory Management
- Agent instance per container (not per request)
- Session state management
- Streaming prevents large response buffering

### Scalability Patterns
- Stateless agent instances
- External session storage (Redis/DynamoDB)
- Horizontal scaling via container instances

## Integration Points

### Authentication Gateway
```python
# src/gateway/agentcore.py
class AgentCoreGitHubAuth:
    async def get_token() -> str:
        # Integrates with AgentCore Identity provider
        return await credential_provider.get_token()
```

### Tool Integration
```python
# Tools automatically available to agent
from src.tools.github_tools import GitHubTools
from src.tools.github_tools_hybrid import GitHubToolsHybrid
```

### Session Management
```python
# src/chat/session.py
class SessionManager:
    # Handles conversation state
    # Compatible with AgentCore session semantics
```

## Testing Patterns

### Runtime Testing
```python
@pytest.mark.asyncio
async def test_streaming_response():
    """Test streaming response pattern."""
    async def mock_stream():
        for chunk in ["Response", " ", "chunks"]:
            yield chunk

    responses = []
    async for response in mock_stream():
        responses.append(response)

    assert len(responses) == 3
```

### Integration Testing
```python
def test_payload_handling():
    """Test AgentCore payload structure."""
    payload = {"prompt": "Test request", "session_id": "test123"}

    assert "prompt" in payload
    assert isinstance(payload["prompt"], str)
```

## Common Patterns

### Request Lifecycle
1. **Receive**: AgentCore routes request to entrypoint
2. **Validate**: Check required payload fields
3. **Process**: Agent executes business logic
4. **Stream**: Return response in chunks
5. **Complete**: Signal end of response

### Session Handling
```python
# Session continuity across requests
if "session_id" in payload:
    session_id = payload["session_id"]
    # Load or create session context
    messages = session_manager.get_messages(session_id)
```

### Error Recovery
```python
# Graceful error handling
try:
    async for chunk in agent(prompt):
        yield chunk
except ValidationError as e:
    yield f"Invalid request: {e}"
except AuthenticationError as e:
    yield f"Authentication failed: {e}"
except Exception as e:
    yield f"Processing error: {e}"
```

This runtime integration provides a clean bridge between Strands agents and AWS BedrockAgentCore, enabling production-ready deployments with proper streaming, authentication, and error handling.