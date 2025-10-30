"""Pytest configuration and shared fixtures."""
import pytest


@pytest.fixture
def mock_github_client_id():
    """Mock GitHub client ID for testing."""
    return "test_client_id_12345"


@pytest.fixture
def mock_github_client_secret():
    """Mock GitHub client secret for testing."""
    return "test_client_secret_67890"


@pytest.fixture
def sample_session_id():
    """Sample session ID for testing."""
    return "test_session_123"


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return "test_user_456"


@pytest.fixture
def sample_repo_name():
    """Sample repository name for testing."""
    return "testuser/testrepo"
