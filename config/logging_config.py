"""Simple logging configuration for the API."""

import logging
import sys
from loguru import logger


def configure_logging(log_file: str | Path, *, verbose_third_party: bool = False) -> None:
    """Configure loguru with basic output.

    Args:
        log_file: Path to log file
        verbose_third_party: Whether to enable verbose third-party logs
    """
    # Remove default logger
    logger.remove()

    # Add file sink
    logger.add(
        log_file,
        rotation="10 MB",
        retention="10 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8"
    )

    # Add stdout sink for development
    logger.add(
        sys.stdout,
        level="DEBUG" if verbose_third_party else "INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        colorize=True
    )

    # Configure standard library logging to use loguru
    logging.basicConfig(handlers=[logging.NullHandler()], level=logging.CRITICAL)