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

        self._previous_logger_level: int | None = None
        self._previous_propagate: bool | None = None

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

        # Preserve the original logger state when starting a new lifecycle.
        if self._active_config is None:
            self._previous_logger_level = logger.level
            self._previous_propagate = logger.propagate

        self._remove_managed_handlers(logger)

        try:
            handlers = build_handlers(config)
        except Exception:
            if self._active_config is None:
                self._restore_logger_state(logger)

            raise

        logger.setLevel(getattr(logging, config.level))
        logger.propagate = False

        for handler in handlers.values():
            logger.addHandler(handler)

        self._managed_handlers = list(handlers.values())
        self._active_config = config

        return logger

    def shutdown(self) -> None:
        """Remove managed handlers and restore the original logger state."""

        logger = logging.getLogger(APPLICATION_LOGGER_NAME)

        if self._active_config is None:
            return

        self._remove_managed_handlers(logger)
        self._restore_logger_state(logger)

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

    def _restore_logger_state(
        self,
        logger: logging.Logger,
    ) -> None:
        """Restore the logger's settings from before initialization."""

        if self._previous_logger_level is not None:
            logger.setLevel(self._previous_logger_level)

        if self._previous_propagate is not None:
            logger.propagate = self._previous_propagate

        self._previous_logger_level = None
        self._previous_propagate = None


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
