"""Central initialization and management of application logging."""

import logging

from pqc_inventory.infrastructure.logging.configuration import (
    LoggingConfig,
)
from pqc_inventory.infrastructure.logging.handlers import build_handlers

APPLICATION_LOGGER_NAME = "pqc_inventory"


class LoggingManager:
    """Manage application logging configuration and handler lifecycle."""

    def __init__(self) -> None:
        """Initialize the logging manager state."""

        self._managed_handlers: list[logging.Handler] = []
        self._active_config: LoggingConfig | None = None

    def configure(
        self,
        config: LoggingConfig | None = None,
    ) -> logging.Logger:
        """Configure application logging and return its logger."""

        if config is None:
            config = LoggingConfig()

        if not isinstance(config, LoggingConfig):
            raise TypeError("config must be a LoggingConfig instance.")

        logger = logging.getLogger(APPLICATION_LOGGER_NAME)

        # Reuse an existing configuration when its handlers remain attached.
        if config == self._active_config and all(
            handler in logger.handlers for handler in self._managed_handlers
        ):
            return logger

        self._remove_managed_handlers(logger)

        handlers = build_handlers(config)

        logger.setLevel(getattr(logging, config.level))
        logger.propagate = False

        for handler in handlers.values():
            logger.addHandler(handler)

        self._managed_handlers = list(handlers.values())
        self._active_config = config

        return logger

    def shutdown(self) -> None:
        """Remove and close handlers managed by this instance."""

        logger = logging.getLogger(APPLICATION_LOGGER_NAME)

        self._remove_managed_handlers(logger)
        self._active_config = None

    def _remove_managed_handlers(
        self,
        logger: logging.Logger,
    ) -> None:
        """Remove and close previously registered handlers."""

        for handler in self._managed_handlers:
            if handler in logger.handlers:
                logger.removeHandler(handler)

            handler.close()

        self._managed_handlers.clear()


# Shared application logging manager.
_logging_manager = LoggingManager()


def setup_logging(
    config: LoggingConfig | None = None,
) -> logging.Logger:
    """Initialize application logging."""

    return _logging_manager.configure(config)


def shutdown_logging() -> None:
    """Shut down application logging."""

    _logging_manager.shutdown()
