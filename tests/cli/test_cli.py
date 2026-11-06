"""
Unit tests for the pqc_inventory CLI.
"""

from unittest.mock import Mock
import pytest
from pqc_inventory import cli
from pqc_inventory.commands.constants import EXIT_ERROR


def test_policies_command_does_not_initialize_workspace(monkeypatch):
    """
    Verify that the 'policies' command does not initialize the workspace.
    """
    initialize_workspace = Mock()

    monkeypatch.setattr(
        cli,
        "initialize_workspace",
        initialize_workspace,
    )
    monkeypatch.setitem(
        cli.COMMAND_HANDLERS,
        "policies",
        lambda args: 0,
    )

    exit_code = cli.main(["policies"])

    assert exit_code == 0
    initialize_workspace.assert_not_called()


def test_scan_command_initializes_workspace(monkeypatch):
    """
    Verify that the 'scan' command initializes the workspace before execution.
    """
    # Arrange
    workspace = Mock()
    initialize_workspace = Mock(return_value=workspace)
    run_scan = Mock(return_value=0)

    monkeypatch.setattr(
        cli,
        "initialize_workspace",
        initialize_workspace,
    )

    monkeypatch.setitem(
        cli.COMMAND_HANDLERS,
        "scan",
        run_scan,
    )

    # Act
    exit_code = cli.main(["scan", "--targets", "example.com"])

    # Assert
    assert exit_code == 0
    initialize_workspace.assert_called_once_with()

    args = run_scan.call_args.args[0]
    assert args.workspace is workspace


def test_assess_command_initializes_workspace(monkeypatch):
    """
    Verify that the 'assess' command initializes the workspace before execution.
    """
    workspace = Mock()
    initialize_workspace = Mock(return_value=workspace)
    run_assess = Mock(return_value=0)

    monkeypatch.setattr(
        cli,
        "initialize_workspace",
        initialize_workspace,
    )
    monkeypatch.setitem(
        cli.COMMAND_HANDLERS,
        "assess",
        run_assess,
    )

    exit_code = cli.main(["assess", "--input", "evidence.json", "--policies", "A1"])

    assert exit_code == 0
    initialize_workspace.assert_called_once_with()

    args = run_assess.call_args.args[0]
    assert args.workspace is workspace


def test_workspace_initialization_failure_exits_with_error(monkeypatch, capsys):
    """
    Verify that a failure during workspace initialization results in an error exit.
    """
    initialize_workspace = Mock(side_effect=OSError("Permission denied"))
    run_scan = Mock(return_value=0)

    monkeypatch.setattr(
        cli,
        "initialize_workspace",
        initialize_workspace,
    )
    monkeypatch.setitem(
        cli.COMMAND_HANDLERS,
        "scan",
        run_scan,
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["scan", "--targets", "example.com"])

    assert exc_info.value.code == EXIT_ERROR

    captured = capsys.readouterr()
    assert "Workspace initialization failed" in captured.err

    run_scan.assert_not_called()


def test_help_does_not_initialize_workspace(monkeypatch):
    """
    Verify that the '--help' option does not initialize the workspace.
    """
    initialize_workspace = Mock()

    monkeypatch.setattr(
        cli,
        "initialize_workspace",
        initialize_workspace,
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])

    assert exc_info.value.code == 0
    initialize_workspace.assert_not_called()


def test_version_does_not_initialize_workspace(monkeypatch):
    """
    Verify that the '--version' option does not initialize the workspace.
    """
    initialize_workspace = Mock()

    monkeypatch.setattr(
        cli,
        "initialize_workspace",
        initialize_workspace,
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--version"])

    assert exc_info.value.code == 0
    initialize_workspace.assert_not_called()
