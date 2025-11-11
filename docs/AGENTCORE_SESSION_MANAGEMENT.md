# AgentCore Session Management

Technical patterns for managing conversation state and user interactions in BedrockAgentCore.

## Session Architecture

### Session Context in AgentCore
```python
# AgentCore provides session context automatically
session_data = {
    "session_id": "unique-session-identifier",
    "user_id": "authenticated-user-id",
    "tenant_id": "organization-tenant",
    "conversation_id": "chat-conversation-uuid"
}
```

### Session Manager Implementation
```python
# src/chat/session.py
class SessionManager:
    """Session state management for AgentCore conversations."""

    def __init__(self):
        self._sessions: dict[str, list[ChatMessage]] = {}

    def add_message(self, message: ChatMessage) -> None:
        """Add message to session history."""
        if message.session_id not in self._sessions:
            self._sessions[message.session_id] = []

        self._sessions[message.session_id].append(message)

    def get_messages(self, session_id: str, limit: Optional[int] = None) -> list[ChatMessage]:
        """Retrieve session message history."""
        messages = self._sessions.get(session_id, [])
        return messages[-limit:] if limit else messages
```

## Message Flow Patterns

### 1. Message Reception
```python
# From AgentCore payload
@app.entrypoint
async def invoke(payload: Dict[str, Any]):
    session_id = payload.get("session_id", "default")
    prompt = payload["prompt"]

    # Create user message
    user_message = ChatMessage(
        message=prompt,
        session_id=session_id,
        user_id=await get_user_id()
    )

    session_manager.add_message(user_message)
```

### 2. Agent Response
```python
# Agent response streaming
async for response_chunk in agent(prompt, session_context):
    # Stream real-time response
    yield response_chunk

# After complete response, store it
agent_message = ChatMessage(
        message=full_response,
        session_id=session_id,
        user_id=await get_user_id()
    )
session_manager.add_message(agent_message)
```

### 3. Context Retrieval
```python
async def get_conversation_context(session_id: str) -> list[ChatMessage]:
    """Retrieve conversation history for context."""
    messages = session_manager.get_messages(session_id, limit=10)

    # Format for agent context
    context = []
    for msg in messages:
        context.append({
            "role": "user" if msg.user_id else "assistant",
            "content": msg.message,
            "timestamp": msg.timestamp
        })

    return context
```

## Data Models

### ChatMessage Structure
```python
# src/models/chat.py
class ChatMessage(BaseModel):
    """Message structure for AgentCore conversations."""

    message: str = Field(..., description="Message content")
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = Field(None, description="Additional context")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Review PR #123 in the agent-tasks folder",
                "session_id": "sess_abc123",
                "user_id": "user_github_456",
                "timestamp": "2025-11-11T10:30:00Z",
                "metadata": {"intent": "pr_review", "pr_number": 123}
            }
        }
    }
```

### Status Tracking
```python
# src/models/status.py
class StatusModel(BaseModel):
    """Status tracking for AgentCore operations."""

    status: str = Field(..., description="Current status")
    current_step: str = Field(..., description="Current operation")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    issues: list[str] = Field(default_factory=list, description="Issues encountered")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

## Conversation Patterns

### 1. Sequential Conversation
```python
# User sends message
user_msg = ChatMessage(
    message="Review PR #123 for security issues",
    session_id="security_review_session",
    user_id="user_123"
)

# Agent processes and responds
agent_response = await process_security_review(user_msg.message, context)

# Store both messages
session_manager.add_message(user_msg)
session_manager.add_message(ChatMessage(
    message=agent_response,
    session_id="security_review_session",
    user_id=None  # Agent message
))
```

### 2. Context-Aware Responses
```python
async def generate_contextual_response(prompt: str, session_id: str) -> str:
    """Generate response with conversation context."""

    # Get conversation history
    messages = session_manager.get_messages(session_id, limit=5)

    # Build context for agent
    context = build_agent_context(messages)

    # Generate response with context
    response = await agent.generate(prompt, context=context)

    return response
```

### 3. Multi-Turn Dialogues
```python
# Track conversation flow
async def handle_conversation_turn(payload: Dict[str, Any]) -> AsyncGenerator[str, None]:
    """Handle single conversation turn."""
    session_id = payload.get("session_id")
    user_prompt = payload["prompt"]

    # Add user message to session
    user_message = ChatMessage(
        message=user_prompt,
        session_id=session_id,
        user_id=await get_current_user_id()
    )
    session_manager.add_message(user_message)

    # Get conversation context
    context = await get_conversation_context(session_id)

    # Generate streaming response
    response_chunks = []
    async for chunk in agent.generate_stream(user_prompt, context):
        response_chunks.append(chunk)
        yield chunk

    # Store complete agent response
    full_response = "".join(response_chunks)
    agent_message = ChatMessage(
        message=full_response,
        session_id=session_id,
        user_id=None
    )
    session_manager.add_message(agent_message)
```

## Session Lifecycle Management

### Session Creation
```python
async def create_session(user_id: str, initial_context: dict = None) -> str:
    """Create new conversation session."""
    session_id = f"session_{uuid4().hex[:8]}"

    if initial_context:
        # Store initial context as system message
        context_message = ChatMessage(
            message=f"Session context: {initial_context}",
            session_id=session_id,
            user_id=None,
            metadata={"type": "system", "context": initial_context}
        )
        session_manager.add_message(context_message)

    return session_id
```

### Session Cleanup
```python
async def cleanup_session(session_id: str) -> None:
    """Clean up session resources."""
    if session_id in session_manager._sessions:
        # Archive session before deletion
        await archive_session(session_id)
        del session_manager._sessions[session_id]
```

### Session Persistence
```python
# Production session storage (in-memory fallback)
class SessionManager:
    def __init__(self, storage_backend: Optional[SessionStorage] = None):
        self._sessions: dict[str, list[ChatMessage]] = {}
        self._storage = storage_backend or InMemorySessionStorage()

    async def save_session(self, session_id: str) -> None:
        """Persist session to storage."""
        messages = self._sessions.get(session_id, [])
        await self._storage.save(session_id, messages)

    async def load_session(self, session_id: str) -> None:
        """Load session from storage."""
        messages = await self._storage.load(session_id)
        if messages:
            self._sessions[session_id] = messages
```

## Streaming Response Patterns

### Chunked Streaming
```python
async def stream_agent_response(prompt: str, session_id: str) -> AsyncGenerator[str, None]:
    """Stream agent response in real-time chunks."""

    # Generate response with context
    context = await get_conversation_context(session_id)

    # Stream response
    response_buffer = []
    async for chunk in agent.generate_stream(prompt, context):
        response_buffer.append(chunk)
        yield chunk

    # Store complete response
    full_response = "".join(response_buffer)
    await store_agent_response(session_id, full_response)
```

### Backpressure Handling
```python
async def handle_backpressure(response_stream: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
    """Handle streaming backpressure."""
    try:
        async for chunk in response_stream:
            yield chunk
            # Small delay to prevent overwhelming client
            await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        # Client disconnected
        logging.info("Stream cancelled by client")
        raise
```

## Error Handling

### Session Errors
```python
async def handle_session_error(session_id: str, error: Exception) -> str:
    """Handle session-related errors."""
    error_message = f"Session error: {str(error)}"

    # Log error with context
    logging.error(f"Session {session_id} error: {error}", exc_info=True)

    # Store error in session
    error_msg = ChatMessage(
        message=error_message,
        session_id=session_id,
        user_id=None,
        metadata={"type": "error", "error": str(error)}
    )
    session_manager.add_message(error_msg)

    return error_message
```

### Recovery Patterns
```python
async def recover_session_state(session_id: str) -> bool:
    """Attempt to recover corrupted session state."""
    try:
        # Validate session data
        messages = session_manager.get_messages(session_id)
        if not messages:
            return False

        # Validate message integrity
        for msg in messages:
            if not msg.message or not msg.session_id:
                raise ValueError(f"Invalid message in session {session_id}")

        return True
    except Exception:
        # Reset corrupted session
        if session_id in session_manager._sessions:
            del session_manager._sessions[session_id]
        return False
```

## Performance Considerations

### Memory Management
```python
class SessionManager:
    def __init__(self, max_messages_per_session: int = 100):
        self.max_messages = max_messages_per_session
        self._sessions: dict[str, list[ChatMessage]] = {}

    def add_message(self, message: ChatMessage) -> None:
        """Add message with memory limits."""
        session_id = message.session_id

        if session_id not in self._sessions:
            self._sessions[session_id] = []

        self._sessions[session_id].append(message)

        # Trim old messages if exceeding limit
        if len(self._sessions[session_id]) > self.max_messages:
            self._sessions[session_id] = self._sessions[session_id][-self.max_messages:]
```

### Session Expiration
```python
async def cleanup_expired_sessions(max_age_hours: int = 24) -> None:
    """Clean up sessions older than specified age."""
    cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

    expired_sessions = []
    for session_id, messages in session_manager._sessions.items():
        if messages and messages[-1].timestamp < cutoff_time:
            expired_sessions.append(session_id)

    for session_id in expired_sessions:
        await cleanup_session(session_id)
        logging.info(f"Cleaned up expired session: {session_id}")
```

## Testing Session Management

### Unit Testing
```python
def test_session_creation_and_retrieval():
    """Test basic session operations."""
    manager = SessionManager()

    # Add messages
    msg1 = ChatMessage(message="Hello", session_id="test123")
    msg2 = ChatMessage(message="World", session_id="test123")

    manager.add_message(msg1)
    manager.add_message(msg2)

    # Retrieve messages
    messages = manager.get_messages("test123")
    assert len(messages) == 2
    assert messages[0].message == "Hello"
    assert messages[1].message == "World"
```

### Integration Testing
```python
@pytest.mark.asyncio
async def test_conversation_context_flow():
    """Test conversation context management."""
    manager = SessionManager()

    # Simulate conversation
    user_msg = ChatMessage(message="Review PR #123", session_id="review_session")
    manager.add_message(user_msg)

    # Get context
    context = await get_conversation_context("review_session")
    assert len(context) == 1
    assert context[0]["content"] == "Review PR #123"
```

This session management system provides robust conversation state handling for AgentCore deployments, supporting both development and production use cases with proper error handling, performance optimization, and extensibility.