"""Integration tests for sensitive-data logging protection."""

import json
import logging

from pqc_inventory.infrastructure.logging.configuration import (
    LoggingConfig,
    LogOutputConfig,
)
from pqc_inventory.infrastructure.logging.setup import (
    setup_logging,
    shutdown_logging,
)
from pqc_inventory.infrastructure.logging.filters import (
    SensitiveDataFilter,
)


def _setup_file_logging(tmp_path):
    """Initialize logging with console and file outputs."""

    config = LoggingConfig(
        log_directory=tmp_path,
        outputs=LogOutputConfig(
            console_enabled=True,
            file_enabled=True,
        ),
    )

    return setup_logging(config)


def _flush_handlers(logger):
    """Flush all configured logging handlers."""

    for handler in logger.handlers:
        handler.flush()


def _read_outputs(tmp_path, capsys, filenames):
    """Read console output and selected log files."""

    outputs = {
        "console": capsys.readouterr().err,
    }

    for filename in filenames:
        outputs[filename] = (tmp_path / filename).read_text(encoding="utf-8")

    return outputs


def _assert_secrets_redacted(outputs, secrets):
    """Ensure sensitive values are absent from all outputs."""

    for output in outputs.values():
        for secret in secrets:
            assert secret not in output

        assert "[REDACTED]" in output


def _read_json_records(content):
    """Parse JSON log records."""

    return [json.loads(line) for line in content.splitlines()]


def test_sensitive_data_is_redacted_from_all_outputs(
    tmp_path,
    capsys,
):
    """Redact sensitive values from console and all log files."""

    logger = _setup_file_logging(tmp_path)

    secrets = (
        "mySecretPassword123",
        "sensitiveToken456",
        "privateApiKey789",
    )

    try:
        collection_logger = logging.getLogger("pqc_inventory.collection.tls")

        collection_logger.error(
            "Authentication failed: password=%s token=%s api_key=%s",
            *secrets,
        )

        _flush_handlers(logger)

        outputs = _read_outputs(
            tmp_path,
            capsys,
            (
                "application.log",
                "collection.log",
                "error.log",
            ),
        )

        _assert_secrets_redacted(outputs, secrets)

        collection_records = _read_json_records(outputs["collection.log"])

        error_records = _read_json_records(outputs["error.log"])

        assert any(
            "Authentication failed" in record["message"]
            for record in collection_records
        )

        assert any(record["level"] == "ERROR" for record in error_records)

    finally:
        shutdown_logging()


def test_sensitive_exception_details_are_redacted(
    tmp_path,
    capsys,
):
    """Redact sensitive information contained in exception details."""

    logger = _setup_file_logging(tmp_path)

    secret = "exceptionSecret123"

    try:
        try:
            raise ValueError(f"Authentication failed: password={secret}")
        except ValueError:
            logger.exception("Application operation failed")

        _flush_handlers(logger)

        outputs = _read_outputs(
            tmp_path,
            capsys,
            (
                "application.log",
                "error.log",
            ),
        )

        _assert_secrets_redacted(outputs, (secret,))

    finally:
        shutdown_logging()


def test_sensitive_filter_preserves_original_log_record():
    """Ensure filtering does not modify the original logging record."""

    original_message = "Authentication password=originalSecret"

    record = logging.LogRecord(
        name="pqc_inventory.application",
        level=logging.INFO,
        pathname="service.py",
        lineno=20,
        msg=original_message,
        args=(),
        exc_info=None,
    )

    sanitized_record = SensitiveDataFilter().filter(record)

    assert sanitized_record is not record
    assert "originalSecret" in record.getMessage()
    assert "originalSecret" not in sanitized_record.getMessage()
    assert "[REDACTED]" in sanitized_record.getMessage()
