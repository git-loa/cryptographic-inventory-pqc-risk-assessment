"""Tests for application configuration models."""

import pytest
from pydantic import ValidationError

from pqc_inventory.config.models import (
    WorkspaceConfig,
    WorkspaceDirectories,
)


def test_workspace_directories_defaults() -> None:
    """
    Test that WorkspaceDirectories uses default directory
    names when not provided.
    """
    directories = WorkspaceDirectories()

    assert directories.evidence == "evidence"
    assert directories.assessments == "assessments"
    assert directories.reports == "reports"
    assert directories.logs == "logs"


def test_workspace_directories_accept_custom_names() -> None:
    """
    Test that WorkspaceDirectories accepts custom directory names.
    """
    directories = WorkspaceDirectories(
        evidence="evidence_1",
        assessments="assessments_1",
        reports="reports_1",
        logs="logs_1",
    )

    assert directories.evidence == "evidence_1"
    assert directories.assessments == "assessments_1"


def test_workspace_config_defaults() -> None:
    """
    Test that WorkspaceConfig uses default directory names when not provided.
    """
    configuration = WorkspaceConfig()

    assert configuration.directories.evidence == "evidence"
    assert configuration.directories.reports == "reports"


def test_workspace_directories_reject_empty_names() -> None:
    """
    Test that WorkspaceDirectories rejects empty directory names.
    """
    with pytest.raises(ValidationError):
        WorkspaceDirectories(evidence="")


def test_workspace_directories_reject_unknown_fields() -> None:
    """
    Test that WorkspaceDirectories rejects unknown fields.
    """
    with pytest.raises(ValidationError):
        WorkspaceDirectories(evidences="evidence_1")


@pytest.mark.parametrize(
    "directory_name",
    [
        "../outside",
        "../../important-data",
        "..\\outside",
        "C:\\important-data",
        "/important-data",
        ".",
        "..",
        "CON",
        "NUL",
    ],
)
def test_workspace_directories_reject_unsafe_names(
    directory_name: str,
) -> None:
    """
    Test that WorkspaceDirectories rejects unsafe directory names
    that could escape the workspace or are reserved by the OS.
    """
    with pytest.raises(ValidationError):
        WorkspaceDirectories(evidence=directory_name)


def test_workspace_directories_accept_safe_custom_names() -> None:
    """
    Test that WorkspaceDirectories accepts safe custom directory names.
    """
    directories = WorkspaceDirectories(
        evidence="evidence_2026",
        assessments="security_assessments",
        reports="security-reports",
        logs="application_logs",
    )

    assert directories.evidence == "evidence_2026"
