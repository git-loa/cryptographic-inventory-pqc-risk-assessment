"""Unit tests for the complete workflow CLI command."""

from argparse import Namespace
from types import SimpleNamespace
from unittest.mock import Mock

import pqc_inventory.commands.run as run_command
from pqc_inventory.commands.constants import EXIT_SUCCESS


def make_args(workspace: SimpleNamespace) -> Namespace:
    """Create representative arguments for the workflow command."""

    return Namespace(
        targets=["google.com"],
        targets_file=None,
        port=443,
        policies=["A1"],
        yes=False,
        evidence_output=None,
        assessment_output=None,
        output=None,
        output_dir=None,
        format=None,
        all_formats=False,
        author="Test Author",
        organization="Test Organization",
        workspace=workspace,
    )


def test_build_workflow_request_uses_workspace_defaults(
    monkeypatch,
    tmp_path,
):
    """Verify workflow request construction using workspace defaults."""

    workspace = SimpleNamespace(
        evidence_dir=tmp_path / "evidence",
        assessments_dir=tmp_path / "assessments",
        reports_dir=tmp_path / "reports",
    )

    args = make_args(workspace)

    expected_evidence = workspace.evidence_dir / "tls_scans.json"
    expected_assessment = workspace.assessments_dir / "assessment_runs.json"
    expected_report = workspace.reports_dir / "assessment_report.md"

    monkeypatch.setattr(
        run_command,
        "collect_targets",
        Mock(return_value=["google.com"]),
    )
    monkeypatch.setattr(
        run_command,
        "resolve_policy_selection",
        Mock(return_value=["A1"]),
    )
    monkeypatch.setattr(
        run_command,
        "resolve_command_output_path",
        Mock(
            side_effect=[
                expected_evidence,
                expected_assessment,
                expected_report,
            ]
        ),
    )

    # pylint: disable=protected-access
    request, status = run_command._build_workflow_request(
        args=args,
        report_service=Mock(),
    )

    assert status == EXIT_SUCCESS
    assert request is not None

    assert request.targets == ("google.com",)
    assert request.port == 443
    assert request.policy_ids == ("A1",)

    assert request.output_paths.evidence == expected_evidence
    assert request.output_paths.assessment == expected_assessment
    assert request.output_paths.report == expected_report
    assert request.output_paths.report_directory is None

    assert request.author == "Test Author"
    assert request.organization == "Test Organization"
    assert request.report_format == "markdown"


def test_run_workflow_executes_and_summarizes_request(monkeypatch):
    """Verify workflow execution and result summarization."""

    request = SimpleNamespace(output_paths=Mock())
    workflow_result = Mock()

    repository = Mock()
    report_service = Mock()
    workflow_service = Mock()

    workflow_service.execute.return_value = workflow_result

    monkeypatch.setattr(
        run_command,
        "JSONRepository",
        Mock(return_value=repository),
    )
    monkeypatch.setattr(
        run_command,
        "ReportService",
        Mock(return_value=report_service),
    )
    monkeypatch.setattr(
        run_command,
        "WorkflowService",
        Mock(return_value=workflow_service),
    )
    monkeypatch.setattr(
        run_command,
        "_build_workflow_request",
        Mock(return_value=(request, EXIT_SUCCESS)),
    )

    summarize = Mock(return_value=EXIT_SUCCESS)

    monkeypatch.setattr(
        run_command,
        "summarize_workflow",
        summarize,
    )

    result = run_command.run_workflow(Namespace())

    assert result == EXIT_SUCCESS

    workflow_service.execute.assert_called_once_with(request)

    summarize.assert_called_once_with(
        result=workflow_result,
        output_paths=request.output_paths,
    )
