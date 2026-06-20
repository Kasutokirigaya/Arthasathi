"""Path utilities for the API."""

import os
from pathlib import Path


def server_log_path() -> str:
    """Return the default server log path."""
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    return str(log_dir / "server.log")


def default_claude_workspace_path() -> str:
    """Return a default workspace path (not used in this API but kept for compatibility)."""
    return str(Path.home() / ".aarthsaathi" / "workspace")


def managed_env_path() -> Path:
    """Return managed env path (not used in this API but kept for compatibility)."""
    return Path(__file__).parent.parent / ".env"