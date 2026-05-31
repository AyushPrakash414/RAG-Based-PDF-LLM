"""
Structured logging configuration for the Self-Healing RAG service.

Provides a consistent, structured log format across all modules,
including request IDs, query details, retrieval counts, and verdicts.
"""

import logging
import sys
from typing import Any


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that produces structured, human-readable log lines.

    Format: [TIMESTAMP] [LEVEL] [MODULE] message | key=value ...
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record with structured metadata."""
        base = super().format(record)

        # Append any extra structured fields
        extras: dict[str, Any] = getattr(record, "structured_data", {})
        if extras:
            pairs = " | ".join(f"{k}={v}" for k, v in extras.items())
            return f"{base} | {pairs}"
        return base


def setup_logging(level: str = "INFO") -> None:
    """
    Configure the root logger with structured formatting.

    Args:
        level: The logging level string (e.g., 'DEBUG', 'INFO').
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    formatter = StructuredFormatter(
        fmt="[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates on reload
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("qdrant_client").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger instance.

    Args:
        name: The logger name (typically __name__).

    Returns:
        A configured Logger instance.
    """
    return logging.getLogger(name)


def log_structured(
    logger: logging.Logger,
    level: int,
    message: str,
    **kwargs: Any,
) -> None:
    """
    Emit a log message with additional structured key-value data.

    Args:
        logger: The logger to use.
        level: The logging level (e.g., logging.INFO).
        message: The log message.
        **kwargs: Additional structured fields to include.
    """
    record = logger.makeRecord(
        name=logger.name,
        level=level,
        fn="",
        lno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    record.structured_data = kwargs  # type: ignore[attr-defined]
    logger.handle(record)
