"""Tests for central logging initialization."""

import json
import logging
from logging.handlers import RotatingFileHandler

import pytest

from pqc_inventory.infrastructure.logging.configuration import (
    LoggingConfig,
    LogOutputConfig,
)
from pqc_inventory.infrastructure.logging.setup import (
    APPLICATION_LOGGER_NAME,
    setup_logging,
    shutdown_logging,
)


def get_file_handlers(logger: logging.Logger) -> list[RotatingFileHandler]:
    """Return rotating file handlers managed by the application."""

    return [
        handler
        for handler in logger.handlers
        if isinstance(handler, RotatingFileHandler)
    ]


def test_setup_logging_returns_application_logger(tmp_path):
    """Return the configured application logger."""

    config = LoggingConfig(
        log_directory=tmp_path,
        outputs=LogOutputConfig(
            console_enabled=False,
            file_enabled=True,
        ),
    )

    logger = setup_logging(config)

    try:
        assert logger.name == APPLICATION_LOGGER_NAME
        assert logger.level == logging.INFO
        assert logger.propagate is False

    finally:
        shutdown_logging()


def test_setup_logging_registers_all_file_handlers(tmp_path):
    """Register all configured file handlers."""

    config = LoggingConfig(
        log_directory=tmp_path,
        outputs=LogOutputConfig(
            console_enabled=False,
            file_enabled=True,
        ),
    )

    logger = setup_logging(config)

    try:
        file_handlers = get_file_handlers(logger)

        assert len(file_handlers) == 3

    finally:
        shutdown_logging()


def test_setup_logging_does_not_duplicate_handlers(tmp_path):
    """Repeated initialization must not duplicate handlers."""

    config = LoggingConfig(
        log_directory=tmp_path,
        outputs=LogOutputConfig(
            console_enabled=False,
            file_enabled=True,
        ),
    )

    first_logger = setup_logging(config)

    initial_handlers = get_file_handlers(first_logger)

    second_logger = setup_logging(config)

    try:
        current_handlers = get_file_handlers(second_logger)

        assert first_logger is second_logger
        assert len(current_handlers) == 3
        assert current_handlers == initial_handlers

    finally:
        shutdown_logging()


def test_setup_logging_replaces_previous_configuration(tmp_path):
    """Replace previously managed handlers when configuration changes."""

    first_config = LoggingConfig(
        log_directory=tmp_path / "first",
        outputs=LogOutputConfig(
            console_enabled=False,
            file_enabled=True,
        ),
    )

    second_config = LoggingConfig(
        log_directory=tmp_path / "second",
        level="DEBUG",
        outputs=LogOutputConfig(
            console_enabled=False,
            file_enabled=True,
        ),
    )

    logger = setup_logging(first_config)
    old_handlers = get_file_handlers(logger)

    updated_logger = setup_logging(second_config)

    try:
        new_handlers = get_file_handlers(updated_logger)

        assert logger is updated_logger
        assert updated_logger.level == logging.DEBUG
        assert len(new_handlers) == 3

        assert all(handler not in new_handlers for handler in old_handlers)

    finally:
        shutdown_logging()


def test_setup_logging_preserves_unmanaged_handlers(tmp_path):
    """Do not remove handlers installed by other components."""

    logger = logging.getLogger(APPLICATION_LOGGER_NAME)

    external_handler = logging.NullHandler()
    logger.addHandler(external_handler)

    config = LoggingConfig(
        log_directory=tmp_path,
        outputs=LogOutputConfig(
            console_enabled=False,
            file_enabled=True,
        ),
    )

    try:
        setup_logging(config)

        assert external_handler in logger.handlers

    finally:
        shutdown_logging()

        # The test owns this handler, not LoggingManager.
        logger.removeHandler(external_handler)
        external_handler.close()


def test_setup_logging_rejects_invalid_configuration():
    """Reject objects that are not LoggingConfig instances."""

    with pytest.raises(TypeError):
        setup_logging("invalid")


def test_application_messages_reach_application_log(tmp_path):
    """Write application messages to application.log."""

    config = LoggingConfig(
        log_directory=tmp_path,
        outputs=LogOutputConfig(
            console_enabled=False,
            file_enabled=True,
        ),
    )

    logger = setup_logging(config)

    try:
        application_logger = logging.getLogger("pqc_inventory.application")

        application_logger.info("Application workflow started")

        for handler in get_file_handlers(logger):
            handler.flush()

        log_path = tmp_path / "application.log"
        content = log_path.read_text(encoding="utf-8")

        assert "Application workflow started" in content

    finally:
        shutdown_logging()


def test_collection_messages_reach_collection_log(tmp_path):
    """Route collection messages to their dedicated JSON log."""

    config = LoggingConfig(
        log_directory=tmp_path,
        outputs=LogOutputConfig(
            console_enabled=False,
            file_enabled=True,
        ),
    )

    logger = setup_logging(config)

    try:
        collection_logger = logging.getLogger("pqc_inventory.collection.tls")

        collection_logger.info("TLS collection completed")

        for handler in get_file_handlers(logger):
            handler.flush()

        log_path = tmp_path / "collection.log"

        records = [
            json.loads(line)
            for line in log_path.read_text(encoding="utf-8").splitlines()
        ]

        assert any(
            record["message"] == "TLS collection completed" for record in records
        )

    finally:
        shutdown_logging()


def test_errors_reach_error_log(tmp_path):
    """Route ERROR records to error.log."""

    config = LoggingConfig(
        log_directory=tmp_path,
        outputs=LogOutputConfig(
            console_enabled=False,
            file_enabled=True,
        ),
    )

    logger = setup_logging(config)

    try:
        application_logger = logging.getLogger("pqc_inventory.application")

        application_logger.error("Assessment execution failed")

        for handler in get_file_handlers(logger):
            handler.flush()

        log_path = tmp_path / "error.log"

        records = [
            json.loads(line)
            for line in log_path.read_text(encoding="utf-8").splitlines()
        ]

        assert any(
            record["message"] == "Assessment execution failed"
            and record["level"] == "ERROR"
            for record in records
        )

    finally:
        shutdown_logging()


def test_shutdown_logging_removes_managed_handlers(tmp_path):
    """Remove and close application-managed handlers."""

    config = LoggingConfig(
        log_directory=tmp_path,
        outputs=LogOutputConfig(
            console_enabled=False,
            file_enabled=True,
        ),
    )

    logger = setup_logging(config)
    managed_handlers = get_file_handlers(logger)

    shutdown_logging()

    assert all(handler not in logger.handlers for handler in managed_handlers)

    assert all(handler.stream is None for handler in managed_handlers)


def test_shutdown_logging_is_safe_when_called_repeatedly(tmp_path):
    """Allow logging shutdown to be called multiple times."""

    config = LoggingConfig(
        log_directory=tmp_path,
        outputs=LogOutputConfig(
            console_enabled=False,
            file_enabled=True,
        ),
    )

    logger = setup_logging(config)

    shutdown_logging()
    shutdown_logging()

    assert get_file_handlers(logger) == []


def test_logging_can_be_reinitialized_after_shutdown(tmp_path):
    """Create new handlers when logging is initialized again."""

    config = LoggingConfig(
        log_directory=tmp_path,
        outputs=LogOutputConfig(
            console_enabled=False,
            file_enabled=True,
        ),
    )

    first_logger = setup_logging(config)
    old_handlers = get_file_handlers(first_logger)

    shutdown_logging()

    second_logger = setup_logging(config)
    new_handlers = get_file_handlers(second_logger)

    try:
        assert first_logger is second_logger
        assert len(new_handlers) == 3
        assert all(handler not in new_handlers for handler in old_handlers)
        assert all(handler.stream is None for handler in old_handlers)

    finally:
        shutdown_logging()


def test_reinitialization_does_not_duplicate_log_messages(tmp_path):
    """Ensure messages are written only once after reinitialization."""

    config = LoggingConfig(
        log_directory=tmp_path,
        outputs=LogOutputConfig(
            console_enabled=False,
            file_enabled=True,
        ),
    )

    logger = setup_logging(config)

    shutdown_logging()

    logger = setup_logging(config)

    try:
        application_logger = logging.getLogger("pqc_inventory.application")

        application_logger.info("Lifecycle verification message")

        for handler in get_file_handlers(logger):
            handler.flush()

        log_path = tmp_path / "application.log"
        content = log_path.read_text(encoding="utf-8")

        assert content.count("Lifecycle verification message") == 1

    finally:
        shutdown_logging()
