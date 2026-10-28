"""Reusable JSON persistence for application data."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class JSONRepositoryError(RuntimeError):
    """Raised when a JSON repository operation fails."""


class JSONRepository:
    """Read and write JSON data using filesystem paths."""

    @staticmethod
    def _validate_json_path(path: str | Path) -> Path:
        """Convert a path to Path and require a JSON file extension."""
        destination = Path(path)

        if destination.suffix.lower() != ".json":
            raise ValueError(f"Expected a .json file path, received '{destination}'.")

        if not destination.name:
            raise ValueError("The JSON file path must include a filename.")

        return destination

    def save_json(self, path: str | Path, data: Any) -> None:
        """Write JSON data atomically to the specified path."""
        destination = self._validate_json_path(path)
        temporary_path: Path | None = None

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)

                json.dump(
                    data,
                    temporary_file,
                    indent=2,
                    ensure_ascii=False,
                    allow_nan=False,
                )
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            os.replace(temporary_path, destination)

        except (OSError, TypeError, ValueError) as exc:
            raise JSONRepositoryError(
                f"Failed to save JSON file to '{destination}': {exc}"
            ) from exc

        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    # Do not let a cleanup failure mask the original error.
                    pass

    def load_json(self, path: str | Path) -> Any:
        """Load and return JSON data from the specified path."""
        source = self._validate_json_path(path)

        try:
            with source.open("r", encoding="utf-8") as json_file:
                return json.load(json_file)
        except (OSError, json.JSONDecodeError) as exc:
            raise JSONRepositoryError(
                f"Failed to load JSON file from '{source}': {exc}"
            ) from exc
