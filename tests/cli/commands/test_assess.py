"""Unit tests for the assess command."""

from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

import pqc_inventory.commands.assess as assess_command
from pqc_inventory.commands.constants import (
    EXIT_CANCELLED,
    EXIT_ERROR,
    EXIT_INVALID_INPUT,
    EXIT_PARTIAL,
    EXIT_SUCCESS,
)
from pqc_inventory.storage.json_repository import JSONRepositoryError


def make_assessment_run(*statuses: str) -> dict:
    """Create an assessment run containing the supplied policy statuses."""
    return {
        "assessments": {
            f"A{index}": {"execution_status": status}
            for index, status in enumerate(statuses, start=1)
        }
    }


# ============================================================
# Registered policies
# ============================================================


# pylint: disable=missing-function-docstring
def test_get_registered_policies():
    policies = assess_command.get_registered_policies()

    assert isinstance(policies, tuple)
    assert len(policies) >= 1
    assert policies[0].policy_id == "A1"


# ============================================================
# Policy confirmation
# ============================================================


@pytest.mark.parametrize("response", ["y", "yes"])
def test_confirm_all_policies_accepts_confirmation(response):
    policies = assess_command.get_registered_policies()

    with patch("builtins.input", return_value=response):
        result = assess_command.confirm_all_policies(policies)

    assert result is True


@pytest.mark.parametrize("response", ["n", "", "maybe"])
def test_confirm_all_policies_rejects_confirmation(response):
    policies = assess_command.get_registered_policies()

    with patch("builtins.input", return_value=response):
        result = assess_command.confirm_all_policies(policies)

    assert result is False


# ============================================================
# Policy selection
# ============================================================


def test_resolve_policy_selection_explicit_policies():
    args = Namespace(policies=["A1"], yes=False)

    result = assess_command.resolve_policy_selection(args)

    assert result == ["A1"]


def test_resolve_policy_selection_multiple_policies():
    args = Namespace(policies=["A1", "A2"], yes=False)

    mock_policies = (
        SimpleNamespace(policy_id="A1", policy_name="Policy A1"),
        SimpleNamespace(policy_id="A2", policy_name="Policy A2"),
    )

    with patch(
        "pqc_inventory.commands.assess.get_registered_policies",
        return_value=mock_policies,
    ):
        result = assess_command.resolve_policy_selection(args)

    assert result == ["A1", "A2"]


def test_resolve_policy_selection_yes():
    args = Namespace(policies=None, yes=True)

    result = assess_command.resolve_policy_selection(args)

    assert result == ["A1"]


def test_resolve_policy_selection_user_confirms():
    args = Namespace(policies=None, yes=False)

    with (
        patch(
            "pqc_inventory.commands.assess.sys.stdin.isatty",
            return_value=True,
        ),
        patch(
            "pqc_inventory.commands.assess.confirm_all_policies",
            return_value=True,
        ),
    ):
        result = assess_command.resolve_policy_selection(args)

    assert result == ["A1"]


def test_resolve_policy_selection_user_declines():
    args = Namespace(policies=None, yes=False)

    with (
        patch(
            "pqc_inventory.commands.assess.sys.stdin.isatty",
            return_value=True,
        ),
        patch(
            "pqc_inventory.commands.assess.confirm_all_policies",
            return_value=False,
        ),
    ):
        result = assess_command.resolve_policy_selection(args)

    assert result is None


def test_resolve_policy_selection_non_interactive():
    args = Namespace(policies=None, yes=False)

    with patch(
        "pqc_inventory.commands.assess.sys.stdin.isatty",
        return_value=False,
    ):
        with pytest.raises(ValueError, match="non-interactive mode"):
            assess_command.resolve_policy_selection(args)


def test_resolve_policy_selection_explicit_policies_with_yes():
    args = Namespace(policies=["A1"], yes=True)

    result = assess_command.resolve_policy_selection(args)

    assert result == ["A1"]


def test_resolve_policy_selection_unknown_policy():
    args = Namespace(policies=["A99"], yes=False)

    with pytest.raises(ValueError, match="Unregistered policy IDs"):
        assess_command.resolve_policy_selection(args)


def test_resolve_policy_selection_duplicate_policies():
    args = Namespace(policies=["A1", "A1"], yes=False)

    with pytest.raises(ValueError, match="Duplicate policy IDs"):
        assess_command.resolve_policy_selection(args)


def test_resolve_policy_selection_no_registered_policies():
    args = Namespace(policies=None, yes=True)

    with patch(
        "pqc_inventory.commands.assess.get_registered_policies",
        return_value=(),
    ):
        with pytest.raises(ValueError, match="No assessment policies"):
            assess_command.resolve_policy_selection(args)


# ============================================================
# Assessment result summary
# ============================================================


def test_summarize_assessment_results_all_completed(capsys):
    results = [
        make_assessment_run("completed", "completed"),
        make_assessment_run("completed"),
    ]

    output_path = Path("data/assessments/results.json")

    exit_code = assess_command.summarize_assessment_results(
        results,
        output_path,
    )

    captured = capsys.readouterr()

    assert exit_code == EXIT_SUCCESS
    assert "Targets assessed:       2" in captured.out
    assert "Policy executions:      3" in captured.out
    assert "Completed:              3" in captured.out
    assert "Partial:                0" in captured.out
    assert "Failed:                 0" in captured.out
    assert "Not assessed:           0" in captured.out
    assert str(output_path) in captured.out


@pytest.mark.parametrize(
    "status",
    ["partial", "failed", "not_assessed"],
)
def test_summarize_assessment_results_incomplete_statuses(status):
    results = [make_assessment_run(status)]

    exit_code = assess_command.summarize_assessment_results(
        results,
        Path("data/assessments/results.json"),
    )

    assert exit_code == EXIT_PARTIAL


def test_summarize_assessment_results_mixed_statuses(capsys):
    results = [
        make_assessment_run("completed", "partial"),
        make_assessment_run("failed", "not_assessed"),
        make_assessment_run("completed"),
    ]

    exit_code = assess_command.summarize_assessment_results(
        results,
        Path("data/assessments/results.json"),
    )

    captured = capsys.readouterr()

    assert exit_code == EXIT_PARTIAL
    assert "Targets assessed:       3" in captured.out
    assert "Policy executions:      5" in captured.out
    assert "Completed:              2" in captured.out
    assert "Partial:                1" in captured.out
    assert "Failed:                 1" in captured.out
    assert "Not assessed:           1" in captured.out


# ============================================================
# Assessment command execution
# ============================================================


def test_run_assess_success(monkeypatch):
    """Verify successful execution and workflow stage arguments."""

    args = Namespace(
        input="evidence.json",
        output="assessment.json",
        policies=["A1"],
        yes=False,
    )

    expected_results = [make_assessment_run("completed")]
    expected_output = Path("assessment.json")

    mock_policy_selection = Mock(return_value=["A1"])
    mock_output_path = Mock(return_value=expected_output)
    mock_execute = Mock(return_value=expected_results)
    mock_summary = Mock(return_value=EXIT_SUCCESS)

    monkeypatch.setattr(
        assess_command,
        "resolve_policy_selection",
        mock_policy_selection,
    )
    monkeypatch.setattr(
        assess_command,
        "resolve_output_path",
        mock_output_path,
    )
    monkeypatch.setattr(
        assess_command,
        "execute_assessment",
        mock_execute,
    )
    monkeypatch.setattr(
        assess_command,
        "summarize_assessment_results",
        mock_summary,
    )

    result = assess_command.run_assess(args)

    assert result == EXIT_SUCCESS

    mock_policy_selection.assert_called_once_with(args)
    mock_output_path.assert_called_once_with(
        output_path=args.output,
        allowed_extensions={".json"},
    )
    mock_execute.assert_called_once_with(
        input_path=Path("evidence.json"),
        output_path=expected_output,
        policy_ids=["A1"],
    )
    mock_summary.assert_called_once_with(
        expected_results,
        expected_output,
    )


def test_run_assess_invalid_policy_selection(monkeypatch, capsys):
    """Stop execution when policy selection is invalid."""

    args = Namespace(input="evidence.json", output="assessment.json")

    def raise_error(args):
        raise ValueError("Unregistered policy IDs: A99")

    monkeypatch.setattr(
        assess_command,
        "resolve_policy_selection",
        raise_error,
    )

    result = assess_command.run_assess(args)

    assert result == EXIT_INVALID_INPUT
    assert "Policy selection error" in capsys.readouterr().err


def test_run_assess_policy_selection_cancelled(monkeypatch, capsys):
    """Handle cancellation during policy selection."""

    args = Namespace(input="evidence.json", output="assessment.json")

    monkeypatch.setattr(
        assess_command,
        "resolve_policy_selection",
        lambda args: None,
    )

    result = assess_command.run_assess(args)

    assert result == EXIT_CANCELLED
    assert "Assessment cancelled" in capsys.readouterr().out


def test_run_assess_output_cancelled(monkeypatch, capsys):
    """Handle cancellation during output path approval."""

    args = Namespace(input="evidence.json", output="assessment.json")

    monkeypatch.setattr(
        assess_command,
        "resolve_policy_selection",
        Mock(return_value=["A1"]),
    )
    monkeypatch.setattr(
        assess_command,
        "resolve_output_path",
        Mock(return_value=None),
    )

    result = assess_command.run_assess(args)

    assert result == EXIT_CANCELLED
    assert "Assessment cancelled" in capsys.readouterr().out


def test_run_assess_invalid_input(monkeypatch, capsys):
    """Handle invalid assessment evidence."""

    args = Namespace(input="evidence.json", output="assessment.json")

    monkeypatch.setattr(
        assess_command,
        "resolve_policy_selection",
        Mock(return_value=["A1"]),
    )
    monkeypatch.setattr(
        assess_command,
        "resolve_output_path",
        Mock(return_value=Path("assessment.json")),
    )

    def raise_error(**kwargs):
        raise ValueError("Invalid evidence structure.")

    monkeypatch.setattr(
        assess_command,
        "execute_assessment",
        raise_error,
    )

    result = assess_command.run_assess(args)

    assert result == EXIT_INVALID_INPUT
    assert "Assessment input error" in capsys.readouterr().err


def test_run_assess_repository_error(monkeypatch, capsys):
    """Handle repository errors during assessment."""

    args = Namespace(input="evidence.json", output="assessment.json")

    monkeypatch.setattr(
        assess_command,
        "resolve_policy_selection",
        Mock(return_value=["A1"]),
    )
    monkeypatch.setattr(
        assess_command,
        "resolve_output_path",
        Mock(return_value=Path("assessment.json")),
    )

    def raise_error(**kwargs):
        raise JSONRepositoryError("Unable to save assessment results.")

    monkeypatch.setattr(
        assess_command,
        "execute_assessment",
        raise_error,
    )

    result = assess_command.run_assess(args)

    assert result == EXIT_ERROR
    assert "Assessment error" in capsys.readouterr().err


def test_run_assess_unexpected_error(monkeypatch):
    """Handle unexpected assessment execution errors."""

    args = Namespace(input="evidence.json", output="assessment.json")

    monkeypatch.setattr(
        assess_command,
        "resolve_policy_selection",
        Mock(return_value=["A1"]),
    )
    monkeypatch.setattr(
        assess_command,
        "resolve_output_path",
        Mock(return_value=Path("assessment.json")),
    )

    def raise_error(**kwargs):
        raise RuntimeError("Unexpected failure.")

    monkeypatch.setattr(
        assess_command,
        "execute_assessment",
        raise_error,
    )
    with pytest.raises(RuntimeError, match="Unexpected failure."):
        assess_command.run_assess(args)


def test_run_assess_policy_selection_keyboard_interrupt(monkeypatch, capsys):
    """Handle keyboard interruption during policy selection."""

    args = Namespace(input="evidence.json", output="assessment.json")
    mock_output_path = Mock()
    mock_execute = Mock()

    def raise_interrupt(args):
        raise KeyboardInterrupt

    monkeypatch.setattr(
        assess_command,
        "resolve_policy_selection",
        raise_interrupt,
    )
    monkeypatch.setattr(
        assess_command,
        "resolve_output_path",
        mock_output_path,
    )
    monkeypatch.setattr(
        assess_command,
        "execute_assessment",
        mock_execute,
    )

    result = assess_command.run_assess(args)

    assert result == EXIT_CANCELLED
    assert "Assessment cancelled" in capsys.readouterr().out
    mock_output_path.assert_not_called()
    mock_execute.assert_not_called()


def test_run_assess_output_eoferror(monkeypatch, capsys):
    """Handle EOF while approving the output destination."""

    args = Namespace(input="evidence.json", output="assessment.json")
    mock_execute = Mock()

    monkeypatch.setattr(
        assess_command,
        "resolve_policy_selection",
        Mock(return_value=["A1"]),
    )

    def raise_eoferror(*, output_path, allowed_extensions):
        raise EOFError

    monkeypatch.setattr(
        assess_command,
        "resolve_output_path",
        raise_eoferror,
    )
    monkeypatch.setattr(
        assess_command,
        "execute_assessment",
        mock_execute,
    )

    result = assess_command.run_assess(args)

    assert result == EXIT_CANCELLED
    assert "Assessment cancelled" in capsys.readouterr().out
    mock_execute.assert_not_called()


def test_run_assess_propagates_partial_exit_code(monkeypatch):
    """Propagate the partial assessment exit code."""

    args = Namespace(input="evidence.json", output="assessment.json")
    expected_results = [make_assessment_run("partial")]
    expected_output = Path("assessment.json")

    monkeypatch.setattr(
        assess_command,
        "resolve_policy_selection",
        Mock(return_value=["A1"]),
    )
    monkeypatch.setattr(
        assess_command,
        "resolve_output_path",
        Mock(return_value=expected_output),
    )
    monkeypatch.setattr(
        assess_command,
        "execute_assessment",
        Mock(return_value=expected_results),
    )
    monkeypatch.setattr(
        assess_command,
        "summarize_assessment_results",
        Mock(return_value=EXIT_PARTIAL),
    )

    result = assess_command.run_assess(args)

    assert result == EXIT_PARTIAL
