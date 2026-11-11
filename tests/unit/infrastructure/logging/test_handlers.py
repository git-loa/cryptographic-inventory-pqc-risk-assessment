"""Tests for logging handler construction."""

import json
import logging
from logging.handlers import RotatingFileHandler

import pytest

from pqc_inventory.infrastructure.logging.configuration import (
    LoggingConfig,
    LogOutputConfig,
    LogRotationConfig,
)
from pqc_inventory.infrastructure.logging.handlers import build_handlers


def test_build_handlers_creates_all_default_handlers(tmp_path):
    """Create all configured logging handlers."""

    config = LoggingConfig(log_directory=tmp_path)

    handlers = build_handlers(config)

    try:
        assert set(handlers) == {
            "console",
            "application",
            "collection",
            "error",
        }

        assert isinstance(handlers["application"], RotatingFileHandler)
        assert isinstance(handlers["collection"], RotatingFileHandler)
        assert isinstance(handlers["error"], RotatingFileHandler)

    finally:
        for handler in handlers.values():
            handler.close()


def test_build_handlers_respects_disabled_console(tmp_path):
    """Do not create a console handler when disabled."""

    config = LoggingConfig(
        log_directory=tmp_path,
        outputs=LogOutputConfig(
            console_enabled=False,
            file_enabled=True,
        ),
    )

    handlers = build_handlers(config)

    try:
        assert "console" not in handlers
        assert "application" in handlers

    finally:
        for handler in handlers.values():
            handler.close()


def test_build_handlers_respects_disabled_files(tmp_path):
    """Do not create file handlers when disabled."""

    config = LoggingConfig(
        log_directory=tmp_path,
        outputs=LogOutputConfig(
            console_enabled=True,
            file_enabled=False,
        ),
    )

    handlers = build_handlers(config)

    try:
        assert set(handlers) == {"console"}
        assert not list(tmp_path.iterdir())

    finally:
        for handler in handlers.values():
            handler.close()


def test_rotating_handler_uses_configured_settings(tmp_path):
    """Apply configured rotation settings."""

    config = LoggingConfig(
        log_directory=tmp_path,
        rotation=LogRotationConfig(
            max_bytes=1024,
            backup_count=3,
        ),
    )

    handlers = build_handlers(config)

    try:
        handler = handlers["application"]

        assert isinstance(handler, RotatingFileHandler)
        assert handler.maxBytes == 1024
        assert handler.backupCount == 3

    finally:
        for handler in handlers.values():
            handler.close()


def test_collection_filter_accepts_collection_records(tmp_path):
    """Route collection records to the collection handler."""

    config = LoggingConfig(log_directory=tmp_path)
    handlers = build_handlers(config)

    record = logging.LogRecord(
        name="pqc_inventory.collection.tls",
        level=logging.INFO,
        pathname="tls.py",
        lineno=10,
        msg="TLS scan completed",
        args=(),
        exc_info=None,
    )

    try:
        assert handlers["collection"].filter(record)
        assert handlers["application"].filter(record)

    finally:
        for handler in handlers.values():
            handler.close()


def test_collection_filter_rejects_unrelated_records(tmp_path):
    """Exclude unrelated records from collection.log."""

    config = LoggingConfig(log_directory=tmp_path)
    handlers = build_handlers(config)

    record = logging.LogRecord(
        name="pqc_inventory.assessment",
        level=logging.INFO,
        pathname="assessment.py",
        lineno=20,
        msg="Assessment completed",
        args=(),
        exc_info=None,
    )

    try:
        assert handlers["collection"].filter(record) is False

    finally:
        for handler in handlers.values():
            handler.close()


def test_error_filter_accepts_error_records(tmp_path):
    """Accept ERROR and CRITICAL records."""

    config = LoggingConfig(log_directory=tmp_path)
    handlers = build_handlers(config)

    error_record = logging.LogRecord(
        name="pqc_inventory.application",
        level=logging.ERROR,
        pathname="service.py",
        lineno=30,
        msg="Operation failed",
        args=(),
        exc_info=None,
    )

    critical_record = logging.LogRecord(
        name="pqc_inventory.application",
        level=logging.CRITICAL,
        pathname="service.py",
        lineno=31,
        msg="Critical failure",
        args=(),
        exc_info=None,
    )

    try:
        assert handlers["error"].filter(error_record)
        assert handlers["error"].filter(critical_record)

    finally:
        for handler in handlers.values():
            handler.close()


def test_error_filter_rejects_warning_records(tmp_path):
    """Exclude warnings from error.log."""

    config = LoggingConfig(log_directory=tmp_path)
    handlers = build_handlers(config)

    record = logging.LogRecord(
        name="pqc_inventory.application",
        level=logging.WARNING,
        pathname="service.py",
        lineno=40,
        msg="Warning",
        args=(),
        exc_info=None,
    )

    try:
        assert handlers["error"].filter(record) is False

    finally:
        for handler in handlers.values():
            handler.close()


def test_existing_directory_cannot_be_used_as_log_file(tmp_path):
    """Reject a directory supplied as a log-file destination."""

    (tmp_path / "application.log").mkdir()

    config = LoggingConfig(log_directory=tmp_path)

    with pytest.raises(ValueError, match="regular file"):
        build_handlers(config)


def test_collection_logs_are_json_formatted(tmp_path):
    """Verify that collection records use structured JSON formatting."""

    config = LoggingConfig(log_directory=tmp_path)
    handlers = build_handlers(config)

    record = logging.LogRecord(
        name="pqc_inventory.collection.tls",
        level=logging.INFO,
        pathname="tls.py",
        lineno=50,
        msg="TLS scan completed",
        args=(),
        exc_info=None,
    )

    try:
        formatted = handlers["collection"].formatter.format(record)
        payload = json.loads(formatted)

        assert payload["level"] == "INFO"
        assert payload["message"] == "TLS scan completed"

    finally:
        for handler in handlers.values():
            handler.close()
