# Test Suite Organization

Comprehensive test suite for the AWS Coding Agent project following pytest conventions.

## Directory Structure

```
tests/
├── README.md                   # This file - test organization guide
├── conftest.py                 # Shared pytest fixtures
├── __init__.py                 # Python package marker
│
├── test_config.py              # Configuration and settings tests
├── test_logging.py             # Logging setup tests
├── test_models.py              # Pydantic model validation tests
├── test_prompts.py             # Prompt template tests
├── test_session.py             # Session management tests
│
├── integration/                # Integration tests (component interactions)
│   ├── README.md              # Integration test guidelines
│   └── __init__.py
│
└── e2e/                        # End-to-end tests (full workflows)
    ├── README.md              # E2E test guidelines
    └── __init__.py
```

## Naming Conventions

### Test Files
- **Pattern**: `test_<module>.py`
- **Examples**: `test_config.py`, `test_models.py`, `test_github_tools.py`
- **Location**: Root of `tests/` directory for unit tests

### Test Functions
- **Pattern**: `def test_<feature>_<scenario>():`
- **Examples**:
  - `test_settings_loads_defaults()`
  - `test_model_validates_required_fields()`
  - `test_github_tool_handles_auth_error()`

### Test Classes
- **Pattern**: `class Test<FeatureName>:`
- **Examples**:
  - `class TestPlanModel:`
  - `class TestSessionManager:`
  - `class TestGitHubTools:`
- **Use when**: Grouping related tests for a single feature/component

## Test Categories

### Unit Tests (Root Level)
**Purpose**: Test individual functions and classes in isolation

**Current Coverage**:
- ✅ `test_config.py` (64 lines) - Configuration loading and validation
- ✅ `test_logging.py` (44 lines) - Logging setup and configuration
- ✅ `test_models.py` (137 lines) - Pydantic models (Plan, Status, ChatMessage)
- ✅ `test_prompts.py` (80 lines) - Prompt templates and generation
- ✅ `test_session.py` (111 lines) - Session management and storage

**Total**: 436 lines, 31 tests, 29 passing (93.5%)

### Integration Tests
**Purpose**: Test interactions between components and external services

**Location**: `tests/integration/`

**Recommended Test Files**:
- `test_integration_github_api.py` - GitHub API calls with mock responses
- `test_integration_bedrock.py` - AWS Bedrock model invocation
- `test_integration_oauth.py` - OAuth flow with AgentCore Identity
- `test_integration_agent_tools.py` - Agent + GitHub tools coordination

**Status**: 🚧 Placeholder directory - not yet implemented

### End-to-End Tests
**Purpose**: Test complete user workflows and scenarios

**Location**: `tests/e2e/`

**Recommended Test Files**:
- `test_e2e_oauth_flow.py` - Complete OAuth authentication
- `test_e2e_chat_session.py` - Full chat interaction
- `test_e2e_pr_review.py` - PR review automation workflow
- `test_e2e_deployment.py` - AgentCore deployment verification

**Status**: 🚧 Placeholder directory - not yet implemented

## Running Tests

### All Tests
```bash
# Run entire test suite
pytest tests/ -v

# With coverage report
pytest tests/ --cov=src --cov-report=term-missing
```

### Specific Categories
```bash
# Unit tests only (root level)
pytest tests/test_*.py -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v
```

### Specific Files
```bash
# Single test file
pytest tests/test_models.py -v

# Specific test function
pytest tests/test_models.py::TestPlanModel::test_plan_model_valid -v

# Specific test class
pytest tests/test_models.py::TestPlanModel -v
```

### With Filters
```bash
# Run tests matching pattern
pytest tests/ -k "config" -v

# Run failed tests only
pytest tests/ --lf

# Run with detailed output
pytest tests/ -vv --tb=short
```

## Shared Fixtures

Located in `conftest.py`:

| Fixture | Purpose | Type |
|---------|---------|------|
| `mock_github_client_id` | GitHub OAuth client ID | str |
| `mock_github_client_secret` | GitHub OAuth client secret | str |
| `sample_session_id` | Test session identifier | str |
| `sample_user_id` | Test user identifier | str |
| `sample_repo_name` | Test repository name | str |

### Usage Example
```python
def test_something(mock_github_client_id, sample_session_id):
    # Fixtures automatically injected
    assert mock_github_client_id == "test_client_id_12345"
    assert sample_session_id == "test_session_123"
```

## Test Quality Standards

### Required for All Tests
- ✅ Descriptive names explaining what is tested
- ✅ Clear arrange-act-assert structure
- ✅ Proper fixtures for test data
- ✅ Isolated (no dependencies between tests)
- ✅ Fast execution (< 1s per test for unit tests)

### Unit Test Requirements
- Test single function/method
- Mock external dependencies
- Cover happy path and edge cases
- Test error handling

### Integration Test Requirements
- Test real component interactions
- Use test credentials/mocks for external services
- Verify contract boundaries
- Test failure scenarios

### E2E Test Requirements
- Test complete user scenarios
- Use realistic data and flows
- Verify expected outcomes
- Can be slower (< 30s per test)

## Coverage Goals

| Category | Current | Target |
|----------|---------|--------|
| **Overall** | ~70% | 80%+ |
| **Unit Tests** | 70% | 85%+ |
| **Integration** | 0% | 60%+ |
| **E2E** | 0% | Basic workflows |

## Missing Critical Tests

### High Priority
- ❌ `test_github_tools.py` - GitHub API functions
- ❌ `test_auth.py` - OAuth and authentication
- ❌ `test_stream_handler.py` - Streaming responses
- ❌ `test_agent_creation.py` - Agent factory

### Medium Priority
- ❌ Integration tests for GitHub API
- ❌ Integration tests for Bedrock invocation
- ❌ E2E test for OAuth flow

## Best Practices

### Test Organization
```python
# Good: Descriptive name, clear structure
def test_session_manager_adds_message_to_new_session():
    # Arrange
    manager = SessionManager()
    session_id = "test_123"
    message = ChatMessage(role="user", content="Hello")

    # Act
    manager.add_message(session_id, message)

    # Assert
    messages = manager.get_messages(session_id)
    assert len(messages) == 1
    assert messages[0].content == "Hello"
```

### Test Classes
```python
# Good: Group related tests
class TestSessionManager:
    def test_add_message_creates_session(self):
        ...

    def test_add_multiple_messages_same_session(self):
        ...

    def test_clear_session_removes_messages(self):
        ...
```

### Fixtures
```python
# Good: Reusable test data
@pytest.fixture
def sample_chat_message():
    return ChatMessage(
        role="user",
        content="Test message",
        session_id="test_123"
    )
```

## Continuous Integration

Tests run automatically on:
- Every commit (via pre-commit hooks)
- Every pull request (CI pipeline)
- Before deployment

### CI Commands
```bash
# Format and lint
ruff format src/ tests/
ruff check --fix src/ tests/

# Run tests with coverage
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80

# Type checking
mypy src/
```

## Maintenance

### Adding New Tests
1. Determine category (unit/integration/e2e)
2. Create appropriately named file
3. Follow naming conventions
4. Add fixtures to conftest.py if reusable
5. Update this README if adding new patterns

### Cleaning Test Artifacts
```bash
# Remove cache directories
find tests -name "__pycache__" -exec rm -rf {} +
find tests -name "*.pyc" -delete

# Remove coverage artifacts
rm -rf htmlcov/ .coverage
```

### Test Review Checklist
- [ ] Tests follow naming conventions
- [ ] Tests are properly categorized
- [ ] Fixtures used where appropriate
- [ ] Tests are isolated and independent
- [ ] Coverage maintained or improved
- [ ] No flaky or slow tests added

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Project Testing Strategy](../docs/TESTING.md) *(if exists)*

---

**Last Updated**: 2025-11-06
**Test Pass Rate**: 29/31 (93.5%)
**Coverage**: ~70% (estimated)
