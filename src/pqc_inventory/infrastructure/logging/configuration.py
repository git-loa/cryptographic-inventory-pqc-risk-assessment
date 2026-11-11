"""Configuration models for application logging."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class LogRotationConfig:
    """Configure log file rotation."""

    max_bytes: int = 512 * 1024
    backup_count: int = 3

    def __post_init__(self) -> None:
        """Validate log rotation settings."""

        if (
            isinstance(self.max_bytes, bool)
            or not isinstance(self.max_bytes, int)
            or self.max_bytes <= 0
        ):
            raise ValueError("max_bytes must be a positive integer.")

        if (
            isinstance(self.backup_count, bool)
            or not isinstance(self.backup_count, int)
            or self.backup_count < 0
        ):
            raise ValueError("backup_count must be a non-negative integer.")


@dataclass(frozen=True, slots=True)
class LogOutputConfig:
    """Configure logging output destinations."""

    console_enabled: bool = True
    file_enabled: bool = True

    def __post_init__(self) -> None:
        """Validate logging output settings."""

        if not isinstance(self.console_enabled, bool):
            raise TypeError("console_enabled must be a boolean.")

        if not isinstance(self.file_enabled, bool):
            raise TypeError("file_enabled must be a boolean.")

        if not self.console_enabled and not self.file_enabled:
            raise ValueError("At least one logging output must be enabled.")


@dataclass(frozen=True, slots=True)
class LogFileNames:
    """Define and validate application log filenames."""

    application: str = "application.log"
    collection: str = "collection.log"
    error: str = "error.log"

    def __post_init__(self) -> None:
        """Validate filenames and ensure uniqueness."""

        filenames = (self.application, self.collection, self.error)

        for filename in filenames:
            if not isinstance(filename, str):
                raise TypeError("Log filenames must be strings.")

            if not filename.strip():
                raise ValueError("Log filenames cannot be empty.")

            if filename in {".", ".."} or any(
                character in filename for character in ("/", "\\", "\0")
            ):
                raise ValueError(f"Invalid log filename: {filename!r}.")

        if len(set(filenames)) != len(filenames):
            raise ValueError("Log filenames must be unique.")


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    """Define and validate application logging configuration."""

    VALID_LEVELS: ClassVar[frozenset[str]] = frozenset(
        {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    )

    log_directory: Path = Path("logs")
    level: str = "INFO"

    rotation: LogRotationConfig = field(default_factory=LogRotationConfig)

    outputs: LogOutputConfig = field(default_factory=LogOutputConfig)

    filenames: LogFileNames = field(default_factory=LogFileNames)

    def __post_init__(self) -> None:
        """Validate and normalize logging configuration."""

        self._normalize_log_directory()
        self._validate_level()
        self._validate_nested_configs()

    def _normalize_log_directory(self) -> None:
        """Normalize the configured logging directory."""

        if isinstance(self.log_directory, str):
            directory = Path(self.log_directory)

        elif isinstance(self.log_directory, Path):
            directory = self.log_directory

        else:
            raise TypeError("log_directory must be a pathlib.Path or string.")

        object.__setattr__(
            self,
            "log_directory",
            directory.expanduser(),
        )

    def _validate_level(self) -> None:
        """Normalize and validate the logging level."""

        if not isinstance(self.level, str):
            raise TypeError("Logging level must be a string.")

        normalized_level = self.level.strip().upper()

        if normalized_level not in self.VALID_LEVELS:
            raise ValueError(
                f"Invalid logging level: {self.level!r}. "
                f"Expected one of {sorted(self.VALID_LEVELS)}."
            )

        object.__setattr__(self, "level", normalized_level)

    def _validate_nested_configs(self) -> None:
        """Validate nested logging configuration objects."""

        if not isinstance(self.rotation, LogRotationConfig):
            raise TypeError("rotation must be a LogRotationConfig.")

        if not isinstance(self.outputs, LogOutputConfig):
            raise TypeError("outputs must be a LogOutputConfig.")

        if not isinstance(self.filenames, LogFileNames):
            raise TypeError("filenames must be a LogFileNames.")

    def get_log_path(self, filename: str) -> Path:
        """Return the path of a registered log file."""

        registered = {
            self.filenames.application,
            self.filenames.collection,
            self.filenames.error,
        }

        if filename not in registered:
            raise ValueError(f"Unregistered log filename: {filename!r}.")

        return self.log_directory / filename
