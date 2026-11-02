"""Unit tests for the assess command."""

from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from pqc_inventory.commands.assess import (
    confirm_all_policies,
    get_registered_policies,
    resolve_policy_selection,
    summarize_assessment_results,
)
from pqc_inventory.commands.constants import EXIT_PARTIAL, EXIT_SUCCESS

# ============================================================
# Test Helpers
# ============================================================


def make_assessment_run(*statuses: str) -> dict:
    """Create an assessment run containing the supplied policy statuses."""

    return {
        "schema_version": "1.0",
        "assessment_run_id": "test-run",
        "domain": "example.com",
        "created_at": "2026-01-01T00:00:00Z",
        "methodology_version": "1.0",
        "evidence": {},
        "assessments": {
            f"A{index}": {
                "policy_id": f"A{index}",
                "policy_version": "1.0",
                "execution_status": status,
                "findings": [],
                "limitations": [],
            }
            for index, status in enumerate(statuses, start=1)
        },
    }


# ============================================================
# get_registered_policies()
# ============================================================


# pylint: disable=missing-function-docstring
def test_get_registered_policies():
    policies = get_registered_policies()

    assert isinstance(policies, tuple)
    assert len(policies) >= 1
    assert policies[0].policy_id == "A1"


# ============================================================
# confirm_all_policies()
# ============================================================


def test_confirm_all_policies_user_accepts():
    policies = get_registered_policies()

    with patch("builtins.input", return_value="y"):
        result = confirm_all_policies(policies)

    assert result is True


def test_confirm_all_policies_user_accepts_yes():
    policies = get_registered_policies()

    with patch("builtins.input", return_value="yes"):
        result = confirm_all_policies(policies)

    assert result is True


def test_confirm_all_policies_user_declines():
    policies = get_registered_policies()

    with patch("builtins.input", return_value="n"):
        result = confirm_all_policies(policies)

    assert result is False


def test_confirm_all_policies_empty_response():
    policies = get_registered_policies()

    with patch("builtins.input", return_value=""):
        result = confirm_all_policies(policies)

    assert result is False


def test_confirm_all_policies_invalid_response():
    policies = get_registered_policies()

    with patch("builtins.input", return_value="maybe"):
        result = confirm_all_policies(policies)

    assert result is False


# ============================================================
# resolve_policy_selection()
# ============================================================


def test_resolve_policy_selection_explicit_policies():
    args = Namespace(policies=["A1"], yes=False)

    result = resolve_policy_selection(args)

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
        result = resolve_policy_selection(args)

    assert result == ["A1", "A2"]


def test_resolve_policy_selection_yes():
    args = Namespace(policies=None, yes=True)

    result = resolve_policy_selection(args)

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
        result = resolve_policy_selection(args)

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
        result = resolve_policy_selection(args)

    assert result is None


def test_resolve_policy_selection_non_interactive():
    args = Namespace(policies=None, yes=False)

    with patch(
        "pqc_inventory.commands.assess.sys.stdin.isatty",
        return_value=False,
    ):
        with pytest.raises(ValueError, match="non-interactive mode"):
            resolve_policy_selection(args)


def test_resolve_policy_selection_explicit_policies_with_yes():
    args = Namespace(policies=["A1"], yes=True)

    result = resolve_policy_selection(args)

    assert result == ["A1"]


def test_resolve_policy_selection_unknown_policy():
    args = Namespace(policies=["A99"], yes=False)

    with pytest.raises(ValueError, match="Unregistered policy IDs"):
        resolve_policy_selection(args)


def test_resolve_policy_selection_duplicate_policies():
    args = Namespace(policies=["A1", "A1"], yes=False)

    with pytest.raises(ValueError, match="Duplicate policy IDs"):
        resolve_policy_selection(args)


def test_resolve_policy_selection_no_registered_policies():
    args = Namespace(policies=None, yes=True)

    with patch(
        "pqc_inventory.commands.assess.get_registered_policies",
        return_value=(),
    ):
        with pytest.raises(ValueError, match="No assessment policies"):
            resolve_policy_selection(args)


# ============================================================
# summarize_assessment_results()
# ============================================================


def test_summarize_assessment_results_all_completed(capsys):
    results = [
        make_assessment_run("completed", "completed"),
        make_assessment_run("completed"),
    ]

    output_path = Path("data/assessments/results.json")

    exit_code = summarize_assessment_results(results, output_path)

    captured = capsys.readouterr()

    assert exit_code == EXIT_SUCCESS
    assert "Targets assessed:       2" in captured.out
    assert "Policy executions:      3" in captured.out
    assert "Completed:              3" in captured.out
    assert "Partial:                0" in captured.out
    assert "Failed:                 0" in captured.out
    assert "Not assessed:           0" in captured.out
    assert str(output_path) in captured.out


def test_summarize_assessment_results_partial():
    results = [make_assessment_run("completed", "partial")]

    exit_code = summarize_assessment_results(
        results,
        Path("data/assessments/results.json"),
    )

    assert exit_code == EXIT_PARTIAL


def test_summarize_assessment_results_failed():
    results = [make_assessment_run("completed", "failed")]

    exit_code = summarize_assessment_results(
        results,
        Path("data/assessments/results.json"),
    )

    assert exit_code == EXIT_PARTIAL


def test_summarize_assessment_results_not_assessed():
    results = [make_assessment_run("not_assessed")]

    exit_code = summarize_assessment_results(
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

    exit_code = summarize_assessment_results(
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
