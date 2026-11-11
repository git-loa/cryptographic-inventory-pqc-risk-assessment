"""Logging formatters with UTC timestamps."""

import json
import logging
from datetime import datetime, timezone
from typing import Any


class UTCFormatter(logging.Formatter):
    """Format conventional log messages using UTC timestamps."""

    def formatTime(
        self,
        record: logging.LogRecord,
        datefmt: str | None = None,
    ) -> str:
        """Convert the record timestamp into UTC."""

        timestamp = datetime.fromtimestamp(
            record.created,
            tz=timezone.utc,
        )

        if datefmt:
            return timestamp.strftime(datefmt)

        return timestamp.isoformat(timespec="milliseconds").replace(
            "+00:00",
            "Z",
        )


class JSONLogFormatter(logging.Formatter):
    """Serialize log records into structured JSON."""

    CORRELATION_FIELDS = (
        "workflow_id",
        "execution_id",
        "operation_id",
    )

    def format(self, record: logging.LogRecord) -> str:
        """Convert a logging record into a JSON string."""

        timestamp = datetime.fromtimestamp(
            record.created,
            tz=timezone.utc,
        )

        payload: dict[str, Any] = {
            "timestamp": timestamp.isoformat(timespec="milliseconds").replace(
                "+00:00",
                "Z",
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        for field in self.CORRELATION_FIELDS:
            value = getattr(record, field, None)

            if value is not None:
                payload[field] = value

        if record.exc_text:
            payload["exception"] = record.exc_text
        elif record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(payload, ensure_ascii=False, default=str)
