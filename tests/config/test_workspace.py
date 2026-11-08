"""Tests for application workspace management."""

from pathlib import Path

from pqc_inventory.config.workspace import Workspace
from pqc_inventory.config.models import WorkspaceConfig


# pylint: disable=missing-function-docstring
def test_workspace_paths(tmp_path: Path) -> None:
    workspace = Workspace(base_dir=tmp_path / "pqc-assessment")

    assert workspace.config_dir == tmp_path / "pqc-assessment" / "config"
    assert workspace.evidence_dir == tmp_path / "pqc-assessment" / "evidence"
    assert workspace.assessments_dir == tmp_path / "pqc-assessment" / "assessments"
    assert workspace.reports_dir == tmp_path / "pqc-assessment" / "reports"
    assert workspace.logs_dir == tmp_path / "pqc-assessment" / "logs"


def test_workspace_creation(tmp_path: Path) -> None:
    workspace = Workspace(base_dir=tmp_path / "pqc-assessment")

    workspace.create()

    assert workspace.config_dir.is_dir()
    assert workspace.evidence_dir.is_dir()
    assert workspace.assessments_dir.is_dir()
    assert workspace.reports_dir.is_dir()
    assert workspace.logs_dir.is_dir()


def test_workspace_creation_is_idempotent(tmp_path: Path) -> None:
    workspace = Workspace(base_dir=tmp_path / "pqc-assessment")

    workspace.create()
    workspace.create()

    assert workspace.base_dir.is_dir()


def test_workspace_uses_default_directory_names(tmp_path: Path) -> None:
    workspace = Workspace(base_dir=tmp_path / "pqc-assessment")

    assert workspace.evidence_dir.name == "evidence"
    assert workspace.assessments_dir.name == "assessments"
    assert workspace.reports_dir.name == "reports"
    assert workspace.logs_dir.name == "logs"


def test_workspace_accepts_custom_directory_names(tmp_path: Path) -> None:
    workspace = Workspace(
        base_dir=tmp_path / "pqc-assessment",
        directories={
            "evidence": "evidence_1",
            "assessments": "assessments_1",
            "reports": "reports_1",
            "logs": "logs_1",
        },
    )

    assert workspace.evidence_dir.name == "evidence_1"
    assert workspace.assessments_dir.name == "assessments_1"
    assert workspace.reports_dir.name == "reports_1"
    assert workspace.logs_dir.name == "logs_1"


def test_workspace_creates_custom_directories(tmp_path: Path) -> None:
    workspace = Workspace(
        base_dir=tmp_path / "pqc-assessment",
        directories={
            "evidence": "evidence_1",
            "assessments": "assessments_1",
            "reports": "reports_1",
            "logs": "logs_1",
        },
    )

    workspace.create()

    assert workspace.evidence_dir.is_dir()
    assert workspace.assessments_dir.is_dir()
    assert workspace.reports_dir.is_dir()
    assert workspace.logs_dir.is_dir()


def test_workspace_from_configuration(tmp_path: Path) -> None:
    configuration = WorkspaceConfig(
        directories={
            "evidence": "evidence_1",
            "assessments": "assessments_1",
            "reports": "reports_1",
            "logs": "logs_1",
        }
    )

    workspace = Workspace.from_config(
        configuration,
        base_dir=tmp_path / "pqc-assessment",
    )

    workspace.create()

    assert workspace.evidence_dir.is_dir()
    assert workspace.assessments_dir.is_dir()
    assert workspace.reports_dir.is_dir()
    assert workspace.logs_dir.is_dir()


def test_install_default_configs(tmp_path: Path) -> None:
    workspace = Workspace(base_dir=tmp_path / "pqc-assessment")

    workspace.install_default_configs()

    assert (workspace.config_dir / "config.yaml").is_file()
    assert (workspace.config_dir / "policies.yaml").is_file()


def test_install_default_configs_does_not_create_other_directories(
    tmp_path: Path,
) -> None:
    workspace = Workspace(base_dir=tmp_path / "pqc-assessment")

    workspace.install_default_configs()

    assert workspace.config_dir.is_dir()
    assert not workspace.evidence_dir.exists()
    assert not workspace.assessments_dir.exists()
    assert not workspace.reports_dir.exists()
    assert not workspace.logs_dir.exists()


def test_install_default_configs_preserves_existing_files(
    tmp_path: Path,
) -> None:
    workspace = Workspace(base_dir=tmp_path / "pqc-assessment")
    workspace.config_dir.mkdir(parents=True)

    config_file = workspace.config_dir / "config.yaml"
    config_file.write_text(
        "custom: true",
        encoding="utf-8",
    )

    workspace.install_default_configs()

    assert config_file.read_text(encoding="utf-8") == "custom: true"
    assert (workspace.config_dir / "policies.yaml").is_file()
