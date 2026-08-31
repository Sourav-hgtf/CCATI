"""Structured JSON Logger (TASK 12).

Provides a factory that returns a standard Python logger configured for
structured JSON output in production and human-readable output in development.
All other modules import `get_logger(name)` instead of calling
`logging.getLogger()` directly so log format is controlled centrally.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from backend.app.core.config import settings


class _JsonFormatter(logging.Formatter):
    """Formatter that serialises each log record to a JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        log_obj: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Propagate any extra fields attached via `extra={}`
        for key, val in record.__dict__.items():
            if key not in (
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno", "module",
                "msecs", "message", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread", "threadName",
            ):
                log_obj[key] = val

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, default=str)


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger wired to the project's log level and format.

    Usage::

        from backend.app.core.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Prediction completed", extra={"request_id": "abc", "latency_ms": 12.4})
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers when module is reimported in tests
    if logger.handlers:
        return logger

    level_name = getattr(settings, "LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    log_format = getattr(settings, "LOG_FORMAT", "json").lower()
    if log_format == "json":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )

    logger.addHandler(handler)
    logger.propagate = False
    return logger
