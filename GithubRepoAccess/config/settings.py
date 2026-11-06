"""Application settings and constants for GitHub Repository Access Validator."""

from enum import Enum
from typing import List


class AccessStatus(str, Enum):
    """Repository access status classifications."""
    ABLE_TO_ACCESS = "ABLE TO ACCESS"
    NOT_ACCESSIBLE = "NOT ACCESSIBLE"
    VALIDATION_ERROR = "VALIDATION ERROR"


# Application Metadata
APP_TITLE = "GitHub Repository Access Validator"
APP_SUBTITLE = "Automating repository access verification for Jenkins-to-Harness migration"
APP_VERSION = "1.0.0"

# GitHub REST API Configuration
GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"
DEFAULT_REQUEST_TIMEOUT = 15  # seconds

# Standard Validation Messages
MSG_ACCESSIBLE = "Repository is accessible."
MSG_NOT_FOUND_OR_INACCESSIBLE = "Repository not found or inaccessible with the supplied credentials."
MSG_INSUFFICIENT_PERMISSIONS = "Access denied or insufficient permissions."
MSG_RATE_LIMIT_EXCEEDED = "GitHub API rate limit exceeded."
MSG_AUTH_FAILED = "Invalid or expired GitHub Personal Access Token (PAT)."
MSG_TIMEOUT = "Connection to GitHub API timed out."
MSG_NETWORK_ERROR = "Unable to connect to GitHub API."
MSG_INVALID_URL = "Invalid GitHub repository URL format."

# Column Name Aliases for Flexible Excel Parsing (lowercase for matching)
REPO_NAME_ALIASES: List[str] = [
    "repository name",
    "repo name",
    "repository",
    "repo",
    "app name",
    "application name",
    "service name",
    "project name",
]

REPO_URL_ALIASES: List[str] = [
    "github url",
    "repository url",
    "repo url",
    "git url",
    "github link",
    "repo link",
    "repository link",
    "url",
    "git repo url",
]

# Generated Output Column Names
COL_ACCESS_STATUS = "Access Status"
COL_HTTP_STATUS = "HTTP Status"
COL_VALIDATION_MESSAGE = "Validation Message"

# Excel Styling Hex Codes
COLOR_SUCCESS_FILL = "D4EDDA"     # Light pastel green
COLOR_SUCCESS_FONT = "155724"     # Dark green
COLOR_DANGER_FILL = "F8D7DA"      # Light pastel red
COLOR_DANGER_FONT = "721C24"      # Dark red
COLOR_WARNING_FILL = "FFF3CD"     # Light pastel orange/yellow
COLOR_WARNING_FONT = "856404"     # Dark orange/brown
COLOR_HEADER_FILL = "1E293B"      # Dark slate blue
COLOR_HEADER_FONT = "FFFFFF"      # White
COLOR_ZEBRA_FILL = "F8FAFC"       # Very light slate for alternating rows
