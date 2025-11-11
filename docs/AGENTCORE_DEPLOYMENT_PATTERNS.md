# AgentCore Deployment Patterns

Technical patterns and best practices for deploying Strands agents to AWS BedrockAgentCore.

## Deployment Architecture

### Container Structure
```
Deployment Container:
├── Runtime Layer (BedrockAgentCoreApp)
│   ├── HTTP endpoint handling
│   ├── Health checks
│   └── Request routing
├── Application Layer (runtime.py)
│   ├── Agent orchestration
│   ├── Session management
│   └── Response streaming
└── Agent Layer (Strands)
    ├── Business logic
    ├── Tool integration
    └── State management
```

### Runtime Configuration
```python
# src/runtime.py - Entry point for AgentCore
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from src.agent.create_agent import create_coding_agent

app = BedrockAgentCoreApp()
_agent = None

def get_agent():
    """Lazy loading pattern for agent instances."""
    global _agent
    if _agent is None:
        _agent = create_coding_agent()
    return _agent

@app.entrypoint
async def invoke(payload: Dict[str, Any]):
    """Main entry point for AgentCore invocations."""
    agent = get_agent()
    async for chunk in agent(payload["prompt"]):
        yield chunk
```

## Configuration Management

### AgentCore Configuration
```yaml
# .bedrock_agentcore.yaml
name: coding-agent
region: ap-southeast-2
runtime: python3.11
entrypoint: src/runtime.py
memory: 2048
timeout: 300

# Identity provider for OAuth
identity_providers:
  - name: github-provider
    type: OAuth2
    config:
      client_id: ${GITHUB_CLIENT_ID}
      client_secret: ${GITHUB_CLIENT_SECRET}

# Runtime settings
disable_memory: true
disable_otel: true
```

### Application Configuration
```python
# src/config.py
class Settings(BaseSettings):
    # AgentCore settings
    github_provider_name: str = "github-provider"
    aws_region: str = "ap-southeast-2"

    # Model configuration
    model_id: str = "anthropic.claude-sonnet-4.5"
    max_tokens: int = 4000
    temperature: float = 0.7

    # GitHub integration
    github_client_id: str
    github_client_secret: SecretStr

    # Development settings
    debug: bool = False
    log_level: str = "INFO"
```

## Build and Deployment Process

### Build Pipeline
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install uv for faster dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen

COPY src/ ./src/

# Expose port for AgentCore
EXPOSE 8080

# Set entrypoint
CMD ["python", "-m", "src.runtime"]
```

### Deployment Commands
```bash
# Configure AgentCore agent
agentcore configure \
  --name coding-agent \
  --region ap-southeast-2 \
  --entrypoint src/runtime.py \
  --disable-memory \
  --disable-otel

# Deploy to AWS
agentcore deploy

# Check deployment status
agentcore status
```

## Production Patterns

### 1. Lazy Loading Pattern
```python
# Prevents cold start issues with heavy initialization
class AgentFactory:
    _instance = None

    @classmethod
    def get_agent(cls):
        if cls._instance is None:
            # Heavy initialization happens here
            cls._instance = create_coding_agent()
        return cls._instance

@app.entrypoint
async def invoke(payload):
    agent = AgentFactory.get_agent()
    # Use agent...
```

### 2. Graceful Degradation
```python
@app.entrypoint
async def invoke(payload):
    try:
        agent = get_agent()
        async for chunk in agent(payload["prompt"]):
            yield chunk
    except Exception as e:
        # Log error but don't crash
        logger.error(f"Agent error: {e}")
        yield f"Error processing request: {str(e)}"
```

### 3. Health Check Implementation
```python
@app.health
async def health_check():
    """Health check for AgentCore load balancer."""
    try:
        # Basic health checks
        agent_ready = _agent is not None
        auth_ready = await check_authentication()

        return {
            "status": "healthy" if agent_ready and auth_ready else "unhealthy",
            "agent": "ready" if agent_ready else "initializing",
            "auth": "ready" if auth_ready else "unavailable"
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## Scaling Patterns

### Horizontal Scaling
```python
# Stateless design enables horizontal scaling
class StatelessAgent:
    def __init__(self):
        # No instance state
        self.tools = GitHubTools()
        self.llm = ClaudeLLM()

    async def process_request(self, prompt, session_id):
        # All state comes from external storage
        context = await session_manager.get_context(session_id)
        response = await self.llm.generate(prompt, context)
        return response
```

### Session Management at Scale
```python
# External session storage for multi-instance deployments
class DistributedSessionManager:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def add_message(self, session_id: str, message: ChatMessage):
        """Store message in Redis."""
        key = f"session:{session_id}"
        await self.redis.lpush(key, message.model_dump_json())
        await self.redis.expire(key, 86400)  # 24 hour TTL

    async def get_messages(self, session_id: str, limit: int = 10):
        """Retrieve messages from Redis."""
        key = f"session:{session_id}"
        messages = await self.redis.lrange(key, -limit, -1)
        return [ChatMessage.model_validate_json(msg) for msg in messages]
```

### Load Balancing Configuration
```yaml
# Application Load Balancer settings
load_balancer:
  target_group_arn: arn:aws:elasticloadbalancing:...
  health_check:
    path: /health
    interval: 30
    timeout: 5
    healthy_threshold: 2
    unhealthy_threshold: 3

# Auto Scaling
auto_scaling:
  min_capacity: 1
  max_capacity: 10
  target_cpu_utilization: 70
  scale_up_cooldown: 300
  scale_down_cooldown: 300
```

## Monitoring and Observability

### Logging Strategy
```python
# src/utils/logging.py
import structlog

logger = structlog.get_logger()

@app.entrypoint
async def invoke(payload):
    request_id = generate_request_id()
    logger.info(
        "Agent request started",
        request_id=request_id,
        session_id=payload.get("session_id")
    )

    try:
        agent = get_agent()
        async for chunk in agent(payload["prompt"]):
            yield chunk
    except Exception as e:
        logger.error(
            "Agent request failed",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise
```

### Metrics Collection
```python
# Custom metrics for AgentCore
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter('agent_requests_total', 'Total agent requests')
REQUEST_DURATION = Histogram('agent_request_duration_seconds', 'Request duration')
ACTIVE_AGENTS = Gauge('active_agents', 'Number of active agent instances')

@app.entrypoint
async def invoke(payload):
    REQUEST_COUNT.inc()
    start_time = time.time()

    try:
        agent = get_agent()
        async for chunk in agent(payload["prompt"]):
            yield chunk
    finally:
        REQUEST_DURATION.observe(time.time() - start_time)
```

### Error Tracking
```python
# Error categorization and tracking
class AgentError(Exception):
    def __init__(self, message: str, error_type: str, context: dict = None):
        super().__init__(message)
        self.error_type = error_type
        self.context = context or {}

# Usage in runtime
try:
    agent = get_agent()
    async for chunk in agent(prompt):
        yield chunk
except ValidationError as e:
    raise AgentError("Invalid input", "validation_error", {"prompt": prompt})
except AuthenticationError as e:
    raise AgentError("Auth failed", "auth_error", {"session_id": session_id})
except Exception as e:
    raise AgentError("Processing error", "unknown_error", {"error": str(e)})
```

## Security Patterns

### 1. Credential Management
```python
# Secure credential handling
class SecureCredentialManager:
    def __init__(self):
        self._credential_cache = {}
        self._cache_ttl = 3600  # 1 hour

    async def get_credentials(self, provider_name: str):
        cache_key = f"creds:{provider_name}"

        # Check cache first
        if cache_key in self._credential_cache:
            cached_time, credentials = self._credential_cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                return credentials

        # Refresh credentials
        credentials = await self._refresh_credentials(provider_name)
        self._credential_cache[cache_key] = (time.time(), credentials)
        return credentials
```

### 2. Input Validation
```python
# Validate AgentCore input payload
class AgentCorePayload(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = Field(None, max_length=100)
    user_id: Optional[str] = Field(None, max_length=100)
    metadata: Optional[dict] = Field(None)

@app.entrypoint
async def invoke(payload: Dict[str, Any]):
    try:
        validated = AgentCorePayload(**payload)
    except ValidationError as e:
        raise AgentError("Invalid payload", "validation_error", {"errors": e.errors()})
```

### 3. Rate Limiting
```python
# Implement rate limiting for abuse prevention
class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.limits = {
            "requests_per_minute": 60,
            "requests_per_hour": 1000
        }

    async def check_rate_limit(self, user_id: str) -> bool:
        current_time = int(time.time())

        # Check minute limit
        minute_key = f"rate_limit:{user_id}:minute:{current_time // 60}"
        minute_count = await self.redis.incr(minute_key)
        await self.redis.expire(minute_key, 60)

        if minute_count > self.limits["requests_per_minute"]:
            return False

        # Check hour limit
        hour_key = f"rate_limit:{user_id}:hour:{current_time // 3600}"
        hour_count = await self.redis.incr(hour_key)
        await self.redis.expire(hour_key, 3600)

        return hour_count <= self.limits["requests_per_hour"]
```

## Testing Deployment

### Integration Testing
```python
# Test AgentCore integration
@pytest.mark.asyncio
async def test_agentcore_integration():
    """Test full AgentCore request flow."""
    payload = {
        "prompt": "Test request",
        "session_id": "test_session"
    }

    # Mock AgentCore environment
    with patch('src.runtime.BedrockAgentCoreApp') as mock_app:
        mock_app.entrypoint = AsyncMock()
        mock_app.entrypoint.return_value = async_generator(["Test", " ", "response"])

        # Test the flow
        responses = []
        async for chunk in mock_app.entrypoint(payload):
            responses.append(chunk)

        assert len(responses) == 3
        assert "".join(responses) == "Test response"
```

### Load Testing
```python
# Performance testing
async def load_test_concurrent_requests(concurrent_users: int = 10):
    """Test concurrent request handling."""
    payload = {"prompt": "Load test request", "session_id": "load_test"}

    async def single_request():
        async with httpx.AsyncClient() as client:
            response = await client.post("/invoke", json=payload)
            return response.status_code

    # Run concurrent requests
    tasks = [single_request() for _ in range(concurrent_users)]
    results = await asyncio.gather(*tasks)

    # Validate all requests succeeded
    assert all(status == 200 for status in results)
```

This deployment guide provides production-ready patterns for AgentCore deployment, covering configuration, scaling, monitoring, security, and testing aspects.