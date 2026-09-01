"""Structured application logging."""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from opentelemetry import trace


class JsonFormatter(logging.Formatter):
    """Format log records as structured JSON.
    Decide which fields from the LogRecord become JSON fields."""

    def format(self, record: logging.LogRecord) -> str:
        current_span = trace.get_current_span()
        span_context = current_span.get_span_context()

        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=UTC,  # datetime.now(UTC).replace(tzinfo=None),
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if span_context.is_valid:
            payload["trace_id"] = format(span_context.trace_id, "032x")
            payload["span_id"] = format(span_context.span_id, "016x")

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )
