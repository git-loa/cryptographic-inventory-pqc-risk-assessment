"""Tests for logging formatters."""

import json
import logging

from pqc_inventory.infrastructure.logging.formatters import (
    JSONLogFormatter,
    UTCFormatter,
)


def create_log_record() -> logging.LogRecord:
    """Create a sample logging record."""

    return logging.LogRecord(
        name="pqc_inventory.collection.tls",
        level=logging.INFO,
        pathname="tls.py",
        lineno=85,
        msg="TLS collection completed",
        args=(),
        exc_info=None,
    )


def test_utc_formatter_uses_utc_timestamp():
    """Format timestamps using UTC."""

    formatter = UTCFormatter("%(asctime)s %(levelname)s %(message)s")
    record = create_log_record()
    record.created = 0

    formatted = formatter.format(record)

    assert formatted.startswith("1970-01-01T00:00:00.000Z")


def test_json_formatter_produces_valid_json():
    """Produce valid structured JSON."""

    formatter = JSONLogFormatter()
    record = create_log_record()

    formatted = formatter.format(record)
    payload = json.loads(formatted)

    assert payload["level"] == "INFO"
    assert payload["logger"] == "pqc_inventory.collection.tls"
    assert payload["message"] == "TLS collection completed"


def test_json_formatter_uses_utc():
    """Include a UTC timestamp in JSON output."""

    formatter = JSONLogFormatter()
    record = create_log_record()
    record.created = 0

    payload = json.loads(formatter.format(record))

    assert payload["timestamp"] == "1970-01-01T00:00:00.000Z"


def test_json_formatter_includes_correlation_identifiers():
    """Preserve available workflow correlation identifiers."""

    formatter = JSONLogFormatter()
    record = create_log_record()

    record.workflow_id = "workflow-001"
    record.execution_id = "execution-001"

    payload = json.loads(formatter.format(record))

    assert payload["workflow_id"] == "workflow-001"
    assert payload["execution_id"] == "execution-001"


def test_json_formatter_omits_missing_correlation_identifiers():
    """Do not include absent correlation identifiers."""

    formatter = JSONLogFormatter()
    record = create_log_record()

    payload = json.loads(formatter.format(record))

    assert "workflow_id" not in payload
    assert "execution_id" not in payload
    assert "operation_id" not in payload
