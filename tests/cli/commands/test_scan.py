"""
Unit test for scan
"""

from argparse import Namespace
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
