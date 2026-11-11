"""Integration tests for logging rotation and backup retention."""

import logging

import pytest

from pqc_inventory.infrastructure.logging.configuration import (
    LoggingConfig,
    LogOutputConfig,
    LogRotationConfig,
)
from pqc_inventory.infrastructure.logging.handlers import build_handlers


@pytest.mark.parametrize(
    ("handler_name", "logger_name", "level"),
    [
        ("application", "pqc_inventory.application", logging.INFO),
        ("collection", "pqc_inventory.collection.tls", logging.INFO),
        ("error", "pqc_inventory.application", logging.ERROR),
    ],
)
def test_log_rotation_and_backup_retention(
    tmp_path,
    handler_name,
    logger_name,
    level,
):
    """Rotate log files and retain no more than three backups."""

    config = LoggingConfig(
        log_directory=tmp_path,
        rotation=LogRotationConfig(
            max_bytes=256,
            backup_count=3,
        ),
        outputs=LogOutputConfig(
            console_enabled=False,
            file_enabled=True,
        ),
    )

    handlers = build_handlers(config)
    handler = handlers[handler_name]

    try:
        for index in range(60):
            record = logging.LogRecord(
                name=logger_name,
                level=level,
                pathname="rotation_test.py",
                lineno=10,
                msg="Rotation test %s: %s",
                args=(index, "X" * 120),
                exc_info=None,
            )

            handler.handle(record)

        handler.flush()

        filename = getattr(config.filenames, handler_name)
        active_log = tmp_path / filename

        # Discover backup files actually created by the handler.
        backups = sorted(tmp_path.glob(f"{filename}.*"))

        # The active log must exist.
        assert active_log.is_file()

        # Exactly three backup files should be retained.
        assert len(backups) == config.rotation.backup_count

        # Every retained backup must be a non-empty file.
        assert all(backup.is_file() and backup.stat().st_size > 0 for backup in backups)

        # A fourth backup must not exist.
        assert not (tmp_path / f"{filename}.4").exists()

    finally:
        for item in handlers.values():
            item.close()
