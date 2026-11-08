"""
Unit test for scan
"""

from argparse import Namespace
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock
import pytest


from pqc_inventory.commands import scan as scan_command


def test_run_scan_unexpected_error(monkeypatch):
    """Allow unexpected scanning errors to propagate."""

    args = Namespace(
        targets=["example.com"],
        targets_file=None,
        port=443,
        output="evidence.json",
    )

    monkeypatch.setattr(
        scan_command,
        "collect_targets",
        Mock(return_value=["example.com"]),
    )

    monkeypatch.setattr(
        scan_command,
        "resolve_command_output_path",
        Mock(return_value=Path("evidence.json")),
    )

    def raise_error(**kwargs):
        raise RuntimeError("Unexpected scanning failure.")

    monkeypatch.setattr(
        scan_command,
        "execute_scan",
        raise_error,
    )

    with pytest.raises(RuntimeError, match="Unexpected scanning failure."):
        scan_command.run_scan(args)


def test_run_scan_uses_workspace_default_output(tmp_path, monkeypatch):
    """Use the workspace evidence directory when no output is supplied."""

    workspace = SimpleNamespace(
        evidence_dir=tmp_path / "evidence",
        assessments_dir=tmp_path / "assessments",
    )

    args = Namespace(
        targets=["example.com"],
        targets_file=None,
        port=443,
        output=None,
        workspace=workspace,
    )

    expected_output = workspace.evidence_dir / "tls_scans.json"

    mock_resolve = Mock(return_value=expected_output)

    monkeypatch.setattr(
        scan_command,
        "collect_targets",
        Mock(return_value=["example.com"]),
    )
    monkeypatch.setattr(
        scan_command,
        "resolve_command_output_path",
        mock_resolve,
    )
    monkeypatch.setattr(
        scan_command,
        "execute_scan",
        Mock(return_value=[]),
    )
    monkeypatch.setattr(scan_command, "save_scan_results", Mock())
    monkeypatch.setattr(scan_command, "summarize_scan_results", Mock(return_value=0))

    scan_command.run_scan(args)

    mock_resolve.assert_called_once_with(
        output_path=expected_output,
        allowed_extensions={".json"},
    )
