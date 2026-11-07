"""Application workspace management."""

import shutil
from importlib.resources import files
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from pqc_inventory.config.paths import BASE_DIR
from pqc_inventory.config.models import WorkspaceConfig


@dataclass(frozen=True)
class Workspace:
    """Manage application workspace directories."""

    DEFAULT_BASE_DIR: ClassVar[Path] = BASE_DIR

    DEFAULT_DIRECTORIES: ClassVar[dict[str, str]] = {
        "evidence": "evidence",
        "assessments": "assessments",
        "reports": "reports",
        "logs": "logs",
    }

    base_dir: Path = DEFAULT_BASE_DIR

    directories: dict[str, str] = field(default_factory=DEFAULT_DIRECTORIES.copy)

    @property
    def config_dir(self) -> Path:
        """Return the path to the configuration directory."""
        return self.base_dir / "config"

    @property
    def evidence_dir(self) -> Path:
        """Return the path to the evidence directory."""
        return self.base_dir / self.directories["evidence"]

    @property
    def assessments_dir(self) -> Path:
        """Return the path to the assessments directory."""
        return self.base_dir / self.directories["assessments"]

    @property
    def reports_dir(self) -> Path:
        """Return the path to the reports directory."""
        return self.base_dir / self.directories["reports"]

    @property
    def logs_dir(self) -> Path:
        """Return the path to the logs directory."""
        return self.base_dir / self.directories["logs"]

    def create(self) -> None:
        """Create the workspace directory structure."""

        directories = (
            self.config_dir,
            self.evidence_dir,
            self.assessments_dir,
            self.reports_dir,
            self.logs_dir,
        )

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_config(
        cls,
        configuration: WorkspaceConfig,
        base_dir: Path = DEFAULT_BASE_DIR,
    ) -> "Workspace":
        """Create a workspace from validated configuration."""

        return cls(
            base_dir=base_dir,
            directories=configuration.directories.model_dump(),
        )

    def install_default_configs(self) -> None:
        """Install default configuration files without overwriting existing files."""

        self.config_dir.mkdir(parents=True, exist_ok=True)

        templates = files("pqc_inventory.templates.config")

        configuration_files = (
            "config.yaml",
            "policies.yaml",
        )

        for filename in configuration_files:
            destination = self.config_dir / filename

            if destination.exists():
                continue

            source = templates.joinpath(filename)

            with source.open("rb") as source_file:
                with destination.open("wb") as destination_file:
                    shutil.copyfileobj(source_file, destination_file)
