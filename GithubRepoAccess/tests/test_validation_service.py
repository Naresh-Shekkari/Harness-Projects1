"""Unit tests for ValidationService and URL validators."""

from unittest.mock import MagicMock
import pandas as pd
import pytest

from config.settings import AccessStatus, COL_ACCESS_STATUS, COL_HTTP_STATUS
from services.github_service import GitHubAuthException, GitHubService
from services.validation_service import ValidationService
from utils.validators import extract_github_owner_and_repo


def test_url_extractor_valid_formats():
    """Verify owner and repo extraction from various URL styles."""
    valid_cases = [
        ("https://github.com/company/payment-service", "company", "payment-service"),
        ("https://github.com/company/payment-service/", "company", "payment-service"),
        ("https://github.com/company/payment-service.git", "company", "payment-service"),
        ("http://github.com/org-name/repo_name", "org-name", "repo_name"),
        ("github.com/user123/my-app", "user123", "my-app"),
        ("git@github.com:enterprise/core-api.git", "enterprise", "core-api"),
    ]

    for raw_url, expected_owner, expected_repo in valid_cases:
        is_valid, owner, repo, msg = extract_github_owner_and_repo(raw_url)
        assert is_valid is True, f"Failed for {raw_url}: {msg}"
        assert owner == expected_owner
        assert repo == expected_repo


def test_url_extractor_invalid_formats():
    """Verify detection of invalid URL formats."""
    invalid_cases = [
        "",
        None,
        "https://gitlab.com/company/repo",
        "https://github.com/",
        "https://github.com/onlyowner",
        "not-a-valid-url-at-all",
    ]

    for raw_url in invalid_cases:
        is_valid, owner, repo, msg = extract_github_owner_and_repo(raw_url)
        assert is_valid is False


def test_validation_service_orchestration():
    """Test full batch validation across multiple repository states."""
    mock_gh = MagicMock(spec=GitHubService)

    # Configure mock responses based on repository name
    def side_effect_check(owner, repo, token):
        if repo == "accessible-repo":
            return AccessStatus.ABLE_TO_ACCESS, 200, "Repository is accessible."
        elif repo == "private-forbidden":
            return AccessStatus.NOT_ACCESSIBLE, 403, "Access denied or insufficient permissions."
        elif repo == "missing-repo":
            return AccessStatus.NOT_ACCESSIBLE, 404, "Repository not found or inaccessible."
        return AccessStatus.VALIDATION_ERROR, 0, "Unexpected"

    mock_gh.check_repository_access.side_effect = side_effect_check

    service = ValidationService(github_service=mock_gh)

    df_input = pd.DataFrame({
        "Repository Name": [
            "accessible-repo",
            "private-forbidden",
            "missing-repo",
            "bad-url-repo",
            "empty-url-repo",
        ],
        "GitHub URL": [
            "https://github.com/company/accessible-repo",
            "https://github.com/company/private-forbidden",
            "https://github.com/company/missing-repo",
            "https://not-github.com/company/bad",
            "",
        ],
        "Lead Developer": ["Alice", "Bob", "Charlie", "David", "Eve"],
    })

    progress_events = []

    def mock_progress(idx, total, name, status):
        progress_events.append((idx, total, name, status))

    results_df, summary = service.validate_repositories(
        df=df_input,
        repo_col="Repository Name",
        url_col="GitHub URL",
        token="ghp_mocktoken",
        progress_callback=mock_progress,
    )

    # Verify original columns preserved
    assert "Lead Developer" in results_df.columns
    assert len(results_df) == 5

    # Check statuses
    statuses = list(results_df[COL_ACCESS_STATUS])
    assert statuses[0] == AccessStatus.ABLE_TO_ACCESS.value
    assert statuses[1] == AccessStatus.NOT_ACCESSIBLE.value
    assert statuses[2] == AccessStatus.NOT_ACCESSIBLE.value
    assert statuses[3] == AccessStatus.VALIDATION_ERROR.value
    assert statuses[4] == AccessStatus.VALIDATION_ERROR.value

    # Check HTTP Statuses
    http_codes = list(results_df[COL_HTTP_STATUS])
    assert http_codes[0] == "200"
    assert http_codes[1] == "403"
    assert http_codes[2] == "404"
    assert http_codes[3] == "N/A"
    assert http_codes[4] == "N/A"

    # Check summary counts
    assert summary["total"] == 5
    assert summary["accessible"] == 1
    assert summary["not_accessible"] == 2
    assert summary["errors"] == 2
    assert summary["success_rate"] == "20.0%"

    # Check that progress events were triggered
    assert len(progress_events) > 0


def test_validation_service_halts_on_401_auth_failure():
    """Verify that validation halts immediately if a 401 is encountered."""
    mock_gh = MagicMock(spec=GitHubService)
    # Simulate valid token on first repo, then expired on second
    mock_gh.check_repository_access.side_effect = [
        (AccessStatus.ABLE_TO_ACCESS, 200, "Repository is accessible."),
        GitHubAuthException("Invalid or expired GitHub Personal Access Token."),
    ]

    service = ValidationService(github_service=mock_gh)

    df_input = pd.DataFrame({
        "Repository Name": ["repo1", "repo2", "repo3", "repo4"],
        "GitHub URL": [
            "https://github.com/company/repo1",
            "https://github.com/company/repo2",
            "https://github.com/company/repo3",
            "https://github.com/company/repo4",
        ],
    })

    with pytest.raises(GitHubAuthException):
        service.validate_repositories(
            df=df_input,
            repo_col="Repository Name",
            url_col="GitHub URL",
            token="ghp_invalid",
        )

    # Ensure only 2 checks were executed before halting (repo3 and repo4 were NOT checked)
    assert mock_gh.check_repository_access.call_count == 2
