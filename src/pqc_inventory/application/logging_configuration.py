"""Application logging configuration resolution."""

import os

from pqc_inventory.infrastructure.logging.configuration import (
    LoggingConfig,
)

ENVIRONMENT_LOG_LEVEL = "PQC_INVENTORY_LOG_LEVEL"


def resolve_logging_config(
    cli_level: str | None = None,
) -> LoggingConfig:
    """Resolve logging configuration using CLI, environment and defaults.

    Precedence:
        1. Explicit CLI logging level.
        2. Environment logging level.
        3. LoggingConfig default (INFO).
    """

    if cli_level is not None:
        return LoggingConfig(level=cli_level)

    environment_level = os.getenv(ENVIRONMENT_LOG_LEVEL)

    if environment_level is not None:
        return LoggingConfig(level=environment_level)

    return LoggingConfig()
