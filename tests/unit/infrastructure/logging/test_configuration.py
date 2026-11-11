"""Tests for logging configuration."""

from pathlib import Path

import pytest

from pqc_inventory.infrastructure.logging.configuration import (
    LoggingConfig,
    LogFileNames,
    LogRotationConfig,
)


def test_default_configuration():
    """Verify default logging settings."""

    config = LoggingConfig()

    assert config.log_directory == Path("logs")
    assert config.level == "INFO"

    assert config.rotation.max_bytes == 512 * 1024
    assert config.rotation.backup_count == 3

    assert config.outputs.console_enabled is True
    assert config.outputs.file_enabled is True

    assert config.filenames.application == "application.log"
    assert config.filenames.collection == "collection.log"
    assert config.filenames.error == "error.log"


def test_string_log_directory_is_converted_to_path():
    """Accept a string as a log directory."""

    config = LoggingConfig(log_directory="custom-logs")

    assert config.log_directory == Path("custom-logs")


def test_nonexistent_log_directory_is_accepted(tmp_path):
    """Accept a prospective logging directory without creating it."""

    directory = tmp_path / "new_logs"

    config = LoggingConfig(log_directory=directory)

    assert config.log_directory == directory
    assert not directory.exists()


def test_logging_level_is_normalized():
    """Normalize logging levels to uppercase."""

    config = LoggingConfig(level="debug")

    assert config.level == "DEBUG"


@pytest.mark.parametrize(
    "level",
    ["INVALID", "", "TRACE", "INFO123"],
)
def test_invalid_logging_level_is_rejected(level):
    """Reject unsupported logging levels."""

    with pytest.raises(ValueError):
        LoggingConfig(level=level)


@pytest.mark.parametrize("max_bytes", [0, -1, True])
def test_invalid_max_bytes_is_rejected(max_bytes):
    """Reject invalid log file sizes."""

    with pytest.raises(ValueError):
        LogRotationConfig(max_bytes=max_bytes)


@pytest.mark.parametrize("backup_count", [-1, True])
def test_invalid_backup_count_is_rejected(backup_count):
    """Reject invalid backup counts."""

    with pytest.raises(ValueError):
        LogRotationConfig(backup_count=backup_count)


def test_duplicate_filenames_are_rejected():
    """Require distinct log filenames."""

    with pytest.raises(ValueError):
        LogFileNames(
            application="application.log",
            collection="application.log",
        )


def test_directory_traversal_filename_is_rejected():
    """Reject filenames containing directory components."""

    with pytest.raises(ValueError):
        LogFileNames(application="../application.log")


def test_log_path():
    """Resolve a registered log filename."""

    config = LoggingConfig(log_directory="logs")

    assert config.get_log_path("application.log") == Path("logs/application.log")


def test_unregistered_log_path_is_rejected():
    """Reject filenames not registered in the configuration."""

    config = LoggingConfig()

    with pytest.raises(ValueError):
        config.get_log_path("other.log")


def test_configuration_is_immutable():
    """Prevent modification after initialization."""

    config = LoggingConfig()

    with pytest.raises(AttributeError):
        config.level = "DEBUG"


def test_invalid_rotation_configuration_is_rejected():
    """Require a valid rotation configuration."""

    with pytest.raises(TypeError):
        LoggingConfig(rotation="invalid")


def test_invalid_output_configuration_is_rejected():
    """Require a valid output configuration."""

    with pytest.raises(TypeError):
        LoggingConfig(outputs="invalid")


def test_invalid_filenames_configuration_is_rejected():
    """Require a valid filename configuration."""

    with pytest.raises(TypeError):
        LoggingConfig(filenames="invalid")
