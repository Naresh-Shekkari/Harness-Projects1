"""Unit tests for GitHub REST API Service."""

from unittest.mock import MagicMock, patch
import pytest
import requests

from config.settings import AccessStatus
from services.github_service import (
    GitHubAuthException,
    GitHubRateLimitException,
    GitHubService,
)


@pytest.fixture
def github_service():
    """Create a GitHubService instance with a mocked session."""
    session = MagicMock(spec=requests.Session)
    return GitHubService(session=session)


def test_validate_token_success(github_service):
    """Test successful token validation returning user profile."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "login": "devops-lead",
        "name": "DevOps Engineer",
        "type": "User",
    }
    github_service.session.get.return_value = mock_resp

    is_valid, user_data, msg = github_service.validate_token("ghp_testtoken12345678901234567890")

    assert is_valid is True
    assert user_data["login"] == "devops-lead"
    assert "devops-lead" in msg


def test_validate_token_401_unauthorized(github_service):
    """Test token validation failure when token is expired or invalid."""
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    github_service.session.get.return_value = mock_resp

    is_valid, user_data, msg = github_service.validate_token("ghp_invalidtoken")

    assert is_valid is False
    assert user_data == {}
    assert "Invalid or expired" in msg


def test_validate_token_rate_limited(github_service):
    """Test token validation failure when rate limit is reached."""
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.headers = {"X-RateLimit-Remaining": "0"}
    mock_resp.text = "API rate limit exceeded"
    github_service.session.get.return_value = mock_resp

    is_valid, user_data, msg = github_service.validate_token("ghp_ratelimited")

    assert is_valid is False
    assert "rate limit" in msg.lower()


def test_validate_token_network_timeout(github_service):
    """Test token validation timeout error handling."""
    github_service.session.get.side_effect = requests.exceptions.Timeout("Request timed out")

    is_valid, user_data, msg = github_service.validate_token("ghp_test")

    assert is_valid is False
    assert "timed out" in msg.lower()


def test_check_repository_access_200_accessible(github_service):
    """Case 1: HTTP 200 -> ABLE TO ACCESS."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    github_service.session.get.return_value = mock_resp

    status, code, msg = github_service.check_repository_access(
        owner="company", repo="payment-service", token="ghp_valid"
    )

    assert status == AccessStatus.ABLE_TO_ACCESS
    assert code == 200
    assert "accessible" in msg.lower()


def test_check_repository_access_404_not_accessible(github_service):
    """Case 2: HTTP 404 -> NOT ACCESSIBLE (not found or inaccessible)."""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    github_service.session.get.return_value = mock_resp

    status, code, msg = github_service.check_repository_access(
        owner="company", repo="secret-backend", token="ghp_valid"
    )

    assert status == AccessStatus.NOT_ACCESSIBLE
    assert code == 404
    assert "not found or inaccessible" in msg.lower()


def test_check_repository_access_403_permission_denied(github_service):
    """Case 3: HTTP 403 -> NOT ACCESSIBLE when permission denied."""
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.headers = {"X-RateLimit-Remaining": "50"}
    mock_resp.text = "Must have admin rights to Repository."
    github_service.session.get.return_value = mock_resp

    status, code, msg = github_service.check_repository_access(
        owner="company", repo="finance-core", token="ghp_valid"
    )

    assert status == AccessStatus.NOT_ACCESSIBLE
    assert code == 403
    assert "insufficient permissions" in msg.lower()


def test_check_repository_access_401_raises_auth_exception(github_service):
    """Case 4: HTTP 401 -> raises GitHubAuthException to halt batch validation."""
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    github_service.session.get.return_value = mock_resp

    with pytest.raises(GitHubAuthException):
        github_service.check_repository_access(
            owner="company", repo="payment-service", token="ghp_expired"
        )


def test_check_repository_access_429_rate_limiting(github_service):
    """Case 6: HTTP 429 -> VALIDATION ERROR rate limit exceeded."""
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {"Retry-After": "60"}
    github_service.session.get.return_value = mock_resp

    status, code, msg = github_service.check_repository_access(
        owner="company", repo="app", token="ghp_valid"
    )

    assert status == AccessStatus.VALIDATION_ERROR
    assert code == 429
    assert "rate limit exceeded" in msg.lower()


def test_check_repository_access_403_rate_limiting_via_header(github_service):
    """Case 6: HTTP 403 with X-RateLimit-Remaining: 0 -> VALIDATION ERROR."""
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1730000000"}
    mock_resp.text = "API rate limit exceeded for user ID"
    github_service.session.get.return_value = mock_resp

    status, code, msg = github_service.check_repository_access(
        owner="company", repo="app", token="ghp_valid"
    )

    assert status == AccessStatus.VALIDATION_ERROR
    assert code == 403
    assert "rate limit exceeded" in msg.lower()


def test_check_repository_access_timeout(github_service):
    """Case 5: Timeout -> VALIDATION ERROR."""
    github_service.session.get.side_effect = requests.exceptions.Timeout("Connection timed out")

    status, code, msg = github_service.check_repository_access(
        owner="company", repo="app", token="ghp_valid"
    )

    assert status == AccessStatus.VALIDATION_ERROR
    assert code == 0
    assert "timed out" in msg.lower()


def test_check_repository_access_network_error(github_service):
    """Case 5: Network connection error -> VALIDATION ERROR."""
    github_service.session.get.side_effect = requests.exceptions.ConnectionError("DNS failure")

    status, code, msg = github_service.check_repository_access(
        owner="company", repo="app", token="ghp_valid"
    )

    assert status == AccessStatus.VALIDATION_ERROR
    assert code == 0
    assert "unable to connect" in msg.lower()
