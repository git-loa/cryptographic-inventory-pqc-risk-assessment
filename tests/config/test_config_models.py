"""Tests for application configuration models."""

import pytest
from pydantic import ValidationError

from pqc_inventory.config.models import (
    WorkspaceConfig,
    WorkspaceDirectories,
)


def test_workspace_directories_defaults() -> None:
    directories = WorkspaceDirectories()

    assert directories.evidence == "evidence"
    assert directories.assessments == "assessments"
    assert directories.reports == "reports"
    assert directories.logs == "logs"


def test_workspace_directories_accept_custom_names() -> None:
    directories = WorkspaceDirectories(
        evidence="evidence_1",
        assessments="assessments_1",
        reports="reports_1",
        logs="logs_1",
    )

    assert directories.evidence == "evidence_1"
    assert directories.assessments == "assessments_1"


def test_workspace_config_defaults() -> None:
    configuration = WorkspaceConfig()

    assert configuration.directories.evidence == "evidence"
    assert configuration.directories.reports == "reports"


def test_workspace_directories_reject_empty_names() -> None:
    with pytest.raises(ValidationError):
        WorkspaceDirectories(evidence="")


def test_workspace_directories_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        WorkspaceDirectories(evidences="evidence_1")
