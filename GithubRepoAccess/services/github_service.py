"""GitHub REST API integration service.

Handles authenticated communication with the GitHub REST API for credential
verification and repository access validation.
"""

from typing import Any, Dict, Optional, Tuple
import requests

from config.settings import (
    AccessStatus,
    DEFAULT_REQUEST_TIMEOUT,
    GITHUB_API_BASE_URL,
    GITHUB_API_VERSION,
    MSG_ACCESSIBLE,
    MSG_AUTH_FAILED,
    MSG_INSUFFICIENT_PERMISSIONS,
    MSG_NETWORK_ERROR,
    MSG_NOT_FOUND_OR_INACCESSIBLE,
    MSG_RATE_LIMIT_EXCEEDED,
    MSG_TIMEOUT,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class GitHubAuthException(Exception):
    """Raised when GitHub returns HTTP 401 Unauthorized, indicating an invalid/expired PAT."""
    pass


class GitHubRateLimitException(Exception):
    """Raised when GitHub returns HTTP 429 or rate limit exhaustion."""
    pass


class GitHubService:
    """Service client for GitHub REST API repository operations."""

    def __init__(
        self,
        base_url: str = GITHUB_API_BASE_URL,
        timeout: int = DEFAULT_REQUEST_TIMEOUT,
        session: Optional[requests.Session] = None,
    ):
        """Initialize the GitHub service.

        Args:
            base_url: Base URL for GitHub API (defaults to https://api.github.com).
            timeout: HTTP request timeout in seconds.
            session: Optional requests.Session instance for connection pooling / testing.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def _get_headers(self, token: str) -> Dict[str, str]:
        """Construct standard GitHub REST API headers with authentication.

        Args:
            token: GitHub Personal Access Token.

        Returns:
            Dictionary of headers.
        """
        clean_token = token.strip() if token else ""
        return {
            "Authorization": f"Bearer {clean_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": "GitHub-Repo-Access-Validator/1.0",
        }

    def validate_token(self, token: str) -> Tuple[bool, Dict[str, Any], str]:
        """Verify that the provided Personal Access Token is valid.

        Calls the /user endpoint to verify token validity and retrieve identity.

        Args:
            token: GitHub Personal Access Token to test.

        Returns:
            Tuple of (is_valid, user_data_dict, message)
        """
        if not token or not token.strip():
            return False, {}, "Personal Access Token is empty."

        url = f"{self.base_url}/user"
        headers = self._get_headers(token)

        try:
            logger.info("Validating GitHub Personal Access Token...")
            response = self.session.get(url, headers=headers, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                login = data.get("login", "Authenticated User")
                name = data.get("name") or login
                user_type = data.get("type", "User")
                msg = f"Successfully authenticated as '{name}' (@{login}) [{user_type}]."
                logger.info("GitHub PAT authentication successful for user: %s", login)
                return True, data, msg

            if response.status_code == 401:
                logger.warning("GitHub PAT validation failed: HTTP 401 Unauthorized.")
                return False, {}, MSG_AUTH_FAILED

            if response.status_code in (403, 429):
                if response.headers.get("X-RateLimit-Remaining") == "0" or "rate limit" in response.text.lower():
                    logger.warning("GitHub rate limit exceeded during token check.")
                    return False, {}, MSG_RATE_LIMIT_EXCEEDED
                return False, {}, f"GitHub authentication returned HTTP {response.status_code}."

            return False, {}, f"GitHub returned unexpected HTTP {response.status_code} during token validation."

        except requests.exceptions.Timeout:
            logger.error("Timeout connecting to GitHub API during token validation.")
            return False, {}, MSG_TIMEOUT
        except requests.exceptions.ConnectionError:
            logger.error("Connection error connecting to GitHub API during token validation.")
            return False, {}, MSG_NETWORK_ERROR
        except requests.exceptions.RequestException as exc:
            logger.error("Request exception during token validation: %s", str(exc))
            return False, {}, f"Network error during authentication: {str(exc)}"

    def check_repository_access(
        self, owner: str, repo: str, token: str
    ) -> Tuple[AccessStatus, int, str]:
        logger.info(f"Checking access for {owner}/{repo}...")
        """Validate whether the authenticated user has access to a specific repository.

        Uses GET https://api.github.com/repos/{owner}/{repo}.

        Args:
            owner: Repository owner / organization name.
            repo: Repository name.
            token: GitHub Personal Access Token.

        Returns:
            Tuple of (AccessStatus, http_status_code, validation_message).

        Raises:
            GitHubAuthException: If HTTP 401 is returned (invalid token).
        """
        if not token or not token.strip():
            raise GitHubAuthException(MSG_AUTH_FAILED)

        url = f"{self.base_url}/repos/{owner}/{repo}"
        headers = self._get_headers(token)

        try:
            response = self.session.get(url, headers=headers, timeout=self.timeout)
            status_code = response.status_code

            # Case 1: HTTP 200 - Able to access
            if status_code == 200:
                return AccessStatus.ABLE_TO_ACCESS, 200, MSG_ACCESSIBLE

            # Case 4: HTTP 401 - Invalid / expired token (HALTS further validation)
            if status_code == 401:
                logger.error("HTTP 401 Unauthorized encountered while checking %s/%s", owner, repo)
                raise GitHubAuthException(MSG_AUTH_FAILED)

            # Case 6: HTTP 429 or HTTP 403 Rate Limiting
            is_rate_limited = (
                status_code == 429
                or (
                    status_code == 403
                    and (
                        response.headers.get("X-RateLimit-Remaining") == "0"
                        or "rate limit" in response.text.lower()
                    )
                )
            )
            if is_rate_limited:
                logger.warning("GitHub API rate limit exceeded for %s/%s", owner, repo)
                reset_time = response.headers.get("X-RateLimit-Reset")
                retry_after = response.headers.get("Retry-After")
                detail = MSG_RATE_LIMIT_EXCEEDED
                if retry_after:
                    detail += f" (Retry-After: {retry_after}s)"
                elif reset_time:
                    detail += f" (Reset epoch: {reset_time})"
                return AccessStatus.VALIDATION_ERROR, status_code, detail

            # Case 3: HTTP 403 - Permission denied (not rate limit)
            if status_code == 403:
                return AccessStatus.NOT_ACCESSIBLE, 403, MSG_INSUFFICIENT_PERMISSIONS

            # Case 2: HTTP 404 - Not found or inaccessible
            if status_code == 404:
                return AccessStatus.NOT_ACCESSIBLE, 404, MSG_NOT_FOUND_OR_INACCESSIBLE

            # Other HTTP statuses (e.g., 500, 502, 503)
            return (
                AccessStatus.VALIDATION_ERROR,
                status_code,
                f"Unexpected HTTP {status_code}: {response.reason or 'GitHub API response error'}",
            )

        except requests.exceptions.Timeout:
            logger.warning("Timeout validating repository %s/%s", owner, repo)
            return AccessStatus.VALIDATION_ERROR, 0, MSG_TIMEOUT

        except requests.exceptions.ConnectionError:
            logger.warning("Connection error validating repository %s/%s", owner, repo)
            return AccessStatus.VALIDATION_ERROR, 0, MSG_NETWORK_ERROR

        except requests.exceptions.RequestException as exc:
            logger.warning("Request exception validating %s/%s: %s", owner, repo, str(exc))
            return AccessStatus.VALIDATION_ERROR, 0, f"API communication error: {str(exc)}"
