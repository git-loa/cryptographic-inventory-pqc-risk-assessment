"""Logging handler construction and configuration."""

import logging
import stat
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pqc_inventory.infrastructure.filesystem.directory_manager import (
    ensure_directory,
)
from pqc_inventory.infrastructure.filesystem.path_safety import (
    validate_path,
)
from pqc_inventory.infrastructure.logging.configuration import (
    LoggingConfig,
)
from pqc_inventory.infrastructure.logging.filters import (
    SensitiveDataFilter,
)
from pqc_inventory.infrastructure.logging.formatters import (
    JSONLogFormatter,
    UTCFormatter,
)


def _validate_log_file(path: Path) -> Path:
    """Validate an existing or prospective log file."""

    candidate = validate_path(path)

    try:
        details = candidate.lstat()
    except FileNotFoundError:
        return candidate

    if not stat.S_ISREG(details.st_mode):
        raise ValueError(f"Log destination must be a regular file: {candidate}")

    return candidate


def _create_rotating_file_handler(
    config: LoggingConfig,
    filename: str,
    formatter: logging.Formatter,
    level: int,
) -> RotatingFileHandler:
    """Create a validated rotating file handler."""

    directory = ensure_directory(config.log_directory)

    log_path = _validate_log_file(directory / config.get_log_path(filename).name)

    handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=config.rotation.max_bytes,
        backupCount=config.rotation.backup_count,
        encoding="utf-8",
    )

    handler.setLevel(level)
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())

    return handler


# pylint: disable=too-few-public-methods
class CollectionLogFilter(logging.Filter):
    """Accept records originating from collection modules."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Identify collection-related log records."""

        return record.name == "pqc_inventory.collection" or record.name.startswith(
            "pqc_inventory.collection."
        )


class ErrorLogFilter(logging.Filter):
    """Accept error and critical log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Accept records with ERROR severity or higher."""

        return record.levelno >= logging.ERROR


def build_handlers(
    config: LoggingConfig,
) -> dict[str, logging.Handler]:
    """Construct the application's configured logging handlers.

    Returns:
        A dictionary containing the enabled logging handlers.
    """

    handlers: dict[str, logging.Handler] = {}

    log_level = getattr(logging, config.level)

    try:
        if config.outputs.console_enabled:
            console_handler = logging.StreamHandler()

            console_handler.setLevel(log_level)
            console_handler.setFormatter(
                UTCFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
            )
            console_handler.addFilter(SensitiveDataFilter())
            handlers["console"] = console_handler

        if config.outputs.file_enabled:
            application_handler = _create_rotating_file_handler(
                config=config,
                filename=config.filenames.application,
                formatter=UTCFormatter(
                    "%(asctime)s %(levelname)s %(name)s: %(message)s"
                ),
                level=log_level,
            )

            handlers["application"] = application_handler

            collection_handler = _create_rotating_file_handler(
                config=config,
                filename=config.filenames.collection,
                formatter=JSONLogFormatter(),
                level=log_level,
            )

            collection_handler.addFilter(CollectionLogFilter())

            handlers["collection"] = collection_handler

            error_handler = _create_rotating_file_handler(
                config=config,
                filename=config.filenames.error,
                formatter=JSONLogFormatter(),
                level=logging.ERROR,
            )

            error_handler.addFilter(ErrorLogFilter())

            handlers["error"] = error_handler

    except Exception:
        for handler in handlers.values():
            handler.close()

        raise

    return handlers
