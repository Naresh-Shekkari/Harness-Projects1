"""Validation service orchestrating GitHub repository access checks.

Manages batch validation execution, progress tracking, URL parsing, error
handling, and authentication failure early-termination.
"""

from typing import Any, Callable, Dict, Optional, Tuple
import pandas as pd

from config.settings import (
    AccessStatus,
    COL_ACCESS_STATUS,
    COL_HTTP_STATUS,
    COL_VALIDATION_MESSAGE,
    MSG_INVALID_URL,
)
from services.github_service import GitHubAuthException, GitHubService
from utils.logger import get_logger
from utils.validators import extract_github_owner_and_repo

logger = get_logger(__name__)

ProgressCallbackType = Optional[Callable[[int, int, str, Optional[str]], None]]


class ValidationService:
    """Orchestrates repository access validation against GitHub REST API."""

    def __init__(self, github_service: Optional[GitHubService] = None):
        """Initialize the validation service.

        Args:
            github_service: Configured GitHubService instance.
        """
        self.github_service = github_service or GitHubService()

    def validate_repositories(
        self,
        df: pd.DataFrame,
        repo_col: str,
        url_col: str,
        token: str,
        progress_callback: ProgressCallbackType = None,
        stop_on_auth_failure: bool = True,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Validate access for all repositories in the DataFrame.

        Iterates sequentially to be gentle on GitHub API rate limits.
        Halts immediately if HTTP 401 Unauthorized occurs.

        Args:
            df: Input DataFrame containing repository records.
            repo_col: Name of column holding repository name.
            url_col: Name of column holding GitHub URL.
            token: GitHub Personal Access Token.
            progress_callback: Optional callable(current_index, total, repo_name, status).

        Returns:
            Tuple of (enriched_DataFrame, summary_stats_dict).

        Raises:
            GitHubAuthException: If authentication fails (HTTP 401) during batch.
        """
        # Create a deep copy to ensure original dataframe is never mutated
        results_df = df.copy()

        access_statuses = []
        http_statuses = []
        messages = []

        total_rows = len(results_df)
        logger.info("Starting validation for %d repositories...", total_rows)

        try:
            for idx, row in results_df.iterrows():
                repo_name = str(row.get(repo_col, f"Row-{idx+1}")).strip()
                raw_url = str(row.get(url_col, "")).strip()

                # Report progress start for this row
                if progress_callback:
                    progress_callback(idx, total_rows, repo_name, None)

                # Check for empty URL
                if not raw_url or raw_url.lower() in ("nan", "none", ""):
                    access_statuses.append(AccessStatus.VALIDATION_ERROR.value)
                    http_statuses.append("N/A")
                    messages.append("GitHub URL is missing or empty.")
                    continue

                # Parse and validate URL
                is_valid, owner, repo, parse_msg = extract_github_owner_and_repo(raw_url)
                if not is_valid:
                    access_statuses.append(AccessStatus.VALIDATION_ERROR.value)
                    http_statuses.append("N/A")
                    messages.append(f"{MSG_INVALID_URL}: {parse_msg}")
                    continue

                # Execute GitHub API access check
                status_enum, http_code, message = self.github_service.check_repository_access(
                    owner=owner, repo=repo, token=token
                )

                access_statuses.append(status_enum.value)
                http_statuses.append(str(http_code) if http_code > 0 else "N/A")
                messages.append(message)

                # Update progress after check
                if progress_callback:
                    progress_callback(idx + 1, total_rows, repo_name, status_enum.value)

        except GitHubAuthException as auth_exc:
            logger.error(
                "Validation halted at record %d/%d due to authentication failure: %s",
                len(access_statuses) + 1,
                total_rows,
                str(auth_exc),
            )
            # Re-raise so the UI controller knows that validation halted due to auth failure
            raise

        # Assign validation result columns
        results_df[COL_ACCESS_STATUS] = access_statuses
        results_df[COL_HTTP_STATUS] = http_statuses
        results_df[COL_VALIDATION_MESSAGE] = messages

        # Calculate statistics
        summary = self.calculate_summary(results_df)
        logger.info(
            "Validation completed: %d total, %d accessible, %d inaccessible, %d errors.",
            summary["total"],
            summary["accessible"],
            summary["not_accessible"],
            summary["errors"],
        )
        return results_df, summary

    @staticmethod
    def calculate_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """Compute summary metrics from a validated DataFrame.

        Args:
            df: DataFrame containing the COL_ACCESS_STATUS column.

        Returns:
            Dictionary with total, accessible, not_accessible, errors, and success_rate.
        """
        if COL_ACCESS_STATUS not in df.columns:
            return {
                "total": len(df),
                "accessible": 0,
                "not_accessible": 0,
                "errors": 0,
                "success_rate": "0.0%",
            }

        total = len(df)
        accessible = int((df[COL_ACCESS_STATUS] == AccessStatus.ABLE_TO_ACCESS.value).sum())
        not_accessible = int((df[COL_ACCESS_STATUS] == AccessStatus.NOT_ACCESSIBLE.value).sum())
        errors = int((df[COL_ACCESS_STATUS] == AccessStatus.VALIDATION_ERROR.value).sum())
        rate = (accessible / total * 100) if total > 0 else 0.0

        return {
            "total": total,
            "accessible": accessible,
            "not_accessible": not_accessible,
            "errors": errors,
            "success_rate": f"{rate:.1f}%",
            "success_rate_num": round(rate, 1),
        }
