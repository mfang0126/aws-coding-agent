# End-to-End Tests

This directory is reserved for end-to-end tests that test the entire application flow.

## Purpose
E2E tests validate complete user scenarios and workflows, such as:
- Full OAuth authentication flow
- Complete chat sessions with agent responses
- PR review automation from start to finish
- AgentCore deployment and invocation

## Test Files
Place E2E test files here following the naming convention:
- `test_e2e_<feature>.py`
- Example: `test_e2e_oauth_flow.py`, `test_e2e_pr_review.py`

## Running E2E Tests
```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run specific E2E test
pytest tests/e2e/test_e2e_oauth_flow.py -v
```

## Requirements
E2E tests may require:
- AWS credentials configured
- GitHub OAuth app credentials
- Running server instance
- External service dependencies

## Status
🚧 Directory placeholder - E2E tests not yet implemented
