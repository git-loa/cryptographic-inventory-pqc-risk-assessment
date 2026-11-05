"""Tests for YAML configuration loading."""

from pathlib import Path

import yaml
import pytest
from pydantic import ValidationError

from pqc_inventory.config.loader import load_config
from pqc_inventory.config.loader import validate_config
from pqc_inventory.config.models import WorkspaceConfig


def test_load_valid_configuration(tmp_path: Path) -> None:
    """Test loading a valid YAML configuration file."""
    config_file = tmp_path / "config.yaml"

    config_file.write_text(
        "application:\n" "  name: PQC Assessment\n" "  version: 0.1.0\n",
        encoding="utf-8",
    )

    configuration = load_config(config_file)

    assert configuration["application"]["name"] == "PQC Assessment"
    assert configuration["application"]["version"] == "0.1.0"


def test_load_empty_configuration_raises_error(tmp_path: Path) -> None:
    """Test loading an empty YAML configuration file raises a ValueError."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a YAML mapping"):
        load_config(config_file)


def test_load_non_mapping_configuration_raises_error(
    tmp_path: Path,
) -> None:
    """
    Test loading a YAML configuration file that is not a
    mapping raises a ValueError.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text("- item1\n- item2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a YAML mapping"):
        load_config(config_file)


def test_load_invalid_yaml_raises_error(tmp_path: Path) -> None:
    """Test loading an invalid YAML configuration file raises a YAMLError."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("application: [invalid", encoding="utf-8")

    with pytest.raises(yaml.YAMLError):
        load_config(config_file)


def test_validate_workspace_configuration() -> None:
    """
    Test validating a valid workspace configuration against
    the WorkspaceConfig model.
    """
    configuration = {
        "directories": {
            "evidence": "evidence_1",
            "assessments": "assessments_1",
            "reports": "reports_1",
            "logs": "logs_1",
        }
    }

    result = validate_config(configuration, WorkspaceConfig)

    assert result.directories.evidence == "evidence_1"
    assert result.directories.reports == "reports_1"


def test_validate_workspace_configuration_rejects_unknown_fields() -> None:
    """
    Test validating a workspace configuration with unknown fields
    """
    configuration = {
        "directories": {
            "evidences": "evidence_1",
        }
    }

    with pytest.raises(ValidationError):
        validate_config(configuration, WorkspaceConfig)
