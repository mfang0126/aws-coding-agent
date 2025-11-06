# Integration Tests

This directory is reserved for integration tests that test interactions between multiple components.

## Purpose
Integration tests validate component interactions and external dependencies, such as:
- GitHub API integration (with real or mocked API)
- AWS Bedrock model invocation
- OAuth provider integration
- Database/session storage integration
- Agent + tools coordination

## Test Files
Place integration test files here following the naming convention:
- `test_integration_<feature>.py`
- Example: `test_integration_github_api.py`, `test_integration_bedrock.py`

## Running Integration Tests
```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific integration test
pytest tests/integration/test_integration_github_api.py -v
```

## Mocking Strategy
Integration tests should:
- Use real external services when feasible (with test credentials)
- Mock external APIs for consistency and speed
- Test actual component boundaries and contracts

## Status
🚧 Directory placeholder - Integration tests not yet implemented
