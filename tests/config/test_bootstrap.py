"""Tests for application workspace initialization."""

from pathlib import Path

from pqc_inventory.config.bootstrap import initialize_workspace
from pqc_inventory.config.workspace import Workspace


def test_initialize_workspace_creates_default_directories(
    tmp_path: Path,
) -> None:
    workspace = initialize_workspace(tmp_path / "pqc-assessment")

    assert workspace.evidence_dir.is_dir()
    assert workspace.assessments_dir.is_dir()
    assert workspace.reports_dir.is_dir()
    assert workspace.logs_dir.is_dir()


def test_initialize_workspace_uses_custom_directories(
    tmp_path: Path,
) -> None:
    base_dir = tmp_path / "pqc-assessment"

    initial_workspace = Workspace(base_dir=base_dir)
    initial_workspace.install_default_configs()

    config_file = initial_workspace.config_dir / "config.yaml"

    config_file.write_text(
        """
workspace:
  directories:
    evidence: evidence_1
    assessments: assessments_1
    reports: reports_1
    logs: logs_1
""",
        encoding="utf-8",
    )

    workspace = initialize_workspace(base_dir)

    assert workspace.evidence_dir.is_dir()
    assert workspace.assessments_dir.is_dir()
    assert workspace.reports_dir.is_dir()
    assert workspace.logs_dir.is_dir()

    assert workspace.evidence_dir.name == "evidence_1"
    assert workspace.assessments_dir.name == "assessments_1"
