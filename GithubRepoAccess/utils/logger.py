"""Security-conscious logging utility.

Ensures sensitive values such as GitHub Personal Access Tokens are never written
to application logs or terminal output.
"""

import logging
import re
import sys
from pathlib import Path
from typing import Optional

# Regex pattern matching common GitHub PAT formats:
# Classic tokens (ghp_...), fine-grained tokens (github_pat_...), OAuth (gho_...), etc.
GITHUB_TOKEN_REGEX = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9_]{36,255}|github_pat_[A-Za-z0-9_]{80,255}|Bearer\s+[A-Za-z0-9_\-\.]+)",
    re.IGNORECASE,
)


def mask_token(token: Optional[str]) -> str:
    """Mask a token for safe reference, returning [REDACTED] or a small preview prefix.

    Args:
        token: Raw token string.

    Returns:
        Masked representation of token.
    """
    if not token:
        return "[EMPTY]"
    clean = token.strip()
    if len(clean) <= 8:
        return "[REDACTED]"
    return f"{clean[:4]}...{clean[-4:]}"


class SensitiveDataScrubber(logging.Filter):
    """Logging filter that scrubs sensitive GitHub tokens from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = GITHUB_TOKEN_REGEX.sub("[TOKEN_REDACTED]", record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: GITHUB_TOKEN_REGEX.sub("[TOKEN_REDACTED]", v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    GITHUB_TOKEN_REGEX.sub("[TOKEN_REDACTED]", a) if isinstance(a, str) else a
                    for a in record.args
                )
        return True


def get_logger(name: str = "github_repo_validator") -> logging.Logger:
    """Configure and return a security-scrubbed logger instance.

    Args:
        name: Name of the logger.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(SensitiveDataScrubber())
        logger.addHandler(console_handler)

        # Optional file handler in logs/ folder if directory exists
        logs_dir = Path(__file__).resolve().parent.parent / "logs"
        if logs_dir.exists():
            file_handler = logging.FileHandler(logs_dir / "app.log", encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.addFilter(SensitiveDataScrubber())
            logger.addHandler(file_handler)

    return logger
