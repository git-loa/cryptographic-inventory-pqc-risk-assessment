"""Tests for application logging configuration resolution."""

import pytest

from pqc_inventory.application.logging_configuration import (
    ENVIRONMENT_LOG_LEVEL,
    resolve_logging_config,
)


def test_default_logging_level_is_info(monkeypatch):
    """Use INFO when no logging level is supplied."""

    monkeypatch.delenv(ENVIRONMENT_LOG_LEVEL, raising=False)

    config = resolve_logging_config()

    assert config.level == "INFO"


def test_environment_logging_level_is_used(monkeypatch):
    """Use the environment logging level when CLI is unspecified."""

    monkeypatch.setenv(ENVIRONMENT_LOG_LEVEL, "DEBUG")

    config = resolve_logging_config()

    assert config.level == "DEBUG"


def test_cli_logging_level_takes_precedence(monkeypatch):
    """Prefer the CLI logging level over the environment."""

    monkeypatch.setenv(ENVIRONMENT_LOG_LEVEL, "WARNING")

    config = resolve_logging_config("DEBUG")

    assert config.level == "DEBUG"


def test_environment_logging_level_is_normalized(monkeypatch):
    """Normalize lowercase environment logging levels."""

    monkeypatch.setenv(ENVIRONMENT_LOG_LEVEL, "debug")

    config = resolve_logging_config()

    assert config.level == "DEBUG"


def test_invalid_environment_logging_level_is_rejected(monkeypatch):
    """Reject unsupported environment logging levels."""

    monkeypatch.setenv(ENVIRONMENT_LOG_LEVEL, "TRACE")

    with pytest.raises(ValueError, match="Invalid logging level"):
        resolve_logging_config()


def test_invalid_cli_logging_level_is_rejected():
    """Reject unsupported CLI logging levels."""

    with pytest.raises(ValueError, match="Invalid logging level"):
        resolve_logging_config("TRACE")
