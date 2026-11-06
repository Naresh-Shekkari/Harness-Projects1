"""Validation utilities for URLs, column names, and repository identifiers."""

import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse

# Pattern matching GitHub URL structures:
# Matches:
#   https://github.com/owner/repo
#   http://github.com/owner/repo.git
#   github.com/owner/repo
#   git@github.com:owner/repo.git
GITHUB_URL_REGEX = re.compile(
    r"^(?:https?://)?(?:www\.)?github\.com[:/](?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)

SSH_GITHUB_REGEX = re.compile(
    r"^git@github\.com:(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


def normalize_column_name(name: str) -> str:
    """Normalize a column header for resilient alias matching.

    Trims whitespace, replaces underscores/hyphens with spaces, and lowercases.

    Args:
        name: Raw column name string.

    Returns:
        Normalized string.
    """
    if not isinstance(name, str):
        return ""
    clean = re.sub(r"[\s_\-]+", " ", name.strip().lower())
    return clean


def find_matching_column(columns: List[str], aliases: List[str]) -> Optional[str]:
    """Find the first column in the list that matches any alias.

    Args:
        columns: Actual column names from Excel.
        aliases: Recognized alias names (lowercase).

    Returns:
        The original column name if found, else None.
    """
    normalized_aliases = [normalize_column_name(a) for a in aliases]
    for col in columns:
        if normalize_column_name(col) in normalized_aliases:
            return col
    return None


def extract_github_owner_and_repo(url: str) -> Tuple[bool, Optional[str], Optional[str], str]:
    """Validate a GitHub URL and extract the owner and repository names.

    Supports HTTPS, HTTP, bare github.com domain, and SSH URLs.
    Handles trailing slashes and .git extensions.

    Args:
        url: The repository URL to validate.

    Returns:
        Tuple of (is_valid, owner, repo, message)
    """
    if not url or not isinstance(url, str):
        return False, None, None, "URL is empty or missing."

    clean_url = url.strip()

    # Try standard HTTP(S) / bare domain pattern
    match = GITHUB_URL_REGEX.match(clean_url)
    if not match:
        # Try SSH pattern
        match = SSH_GITHUB_REGEX.match(clean_url)

    if not match:
        return False, None, None, f"Invalid GitHub URL format: '{clean_url}'."

    owner = match.group("owner").strip()
    repo = match.group("repo").strip()

    # Strip any trailing .git if captured
    if repo.endswith(".git"):
        repo = repo[:-4]

    # Sanity checks on owner and repo
    if not owner or not repo:
        return False, None, None, "Unable to extract owner and repository name from URL."

    # GitHub owners cannot be reserved keywords like 'settings', 'orgs', etc., when at repo level
    reserved = {"settings", "orgs", "features", "explore", "trending", "pricing"}
    if owner.lower() in reserved and not clean_url.startswith("git@"):
        return False, None, None, f"'{owner}' is a reserved GitHub path, not a repository owner."

    return True, owner, repo, "Valid GitHub URL."
