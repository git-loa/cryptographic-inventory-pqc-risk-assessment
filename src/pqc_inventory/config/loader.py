"""YAML configuration loading utilities."""

from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def load_config(path: Path) -> dict[str, Any]:
    """Load and parse a YAML configuration file."""

    with path.open("r", encoding="utf-8") as file:
        configuration = yaml.safe_load(file)

    if not isinstance(configuration, dict):
        raise ValueError(f"Configuration file must contain a YAML mapping: {path}")

    return configuration


def validate_config(
    configuration: dict[str, Any],
    model: type[T],
) -> T:
    """Validate configuration data against a Pydantic model."""

    return model.model_validate(configuration)
