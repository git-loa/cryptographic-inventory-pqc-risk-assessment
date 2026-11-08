"""Unit tests for the complete workflow application service."""

from pathlib import Path
from unittest.mock import Mock, call

import pytest

from pqc_inventory.application.report_request import ReportRequest
from pqc_inventory.application.workflow_request import (
    WorkflowOutputPaths,
    WorkflowRequest,
)
from pqc_inventory.application.workflow_service import (
    WorkflowResult,
    WorkflowService,
)


def make_workflow_request(tmp_path: Path) -> WorkflowRequest:
    """Create a workflow request with temporary output destinations."""

    output_paths = WorkflowOutputPaths(
        evidence=tmp_path / "evidence" / "tls_scans.json",
        assessment=tmp_path / "assessments" / "assessment_runs.json",
        report=tmp_path / "reports" / "assessment_report.md",
    )

    return WorkflowRequest(
        targets=("example.com", "example.org"),
        output_paths=output_paths,
        port=8443,
        policy_ids=("A1",),
        author="Test Author",
        organization="Test Organization",
    )


def test_execute_completes_workflow_in_correct_order(
    tmp_path,
    tls_scan_factory,
    assessment_run_factory,
):
    """Verify successful workflow execution and application-stage ordering."""

    request = make_workflow_request(tmp_path)

    scan_results = [
        tls_scan_factory(scan_id="scan-001", target="example.com"),
        tls_scan_factory(scan_id="scan-002", target="example.org"),
    ]

    assessment_runs = [
        assessment_run_factory(
            assessment_run_id="run-001",
            domain="example.com",
        ),
        assessment_run_factory(
            assessment_run_id="run-002",
            domain="example.org",
        ),
    ]

    expected_report_path = request.output_paths.report

    scan_service = Mock()
    scan_service.scan_many.return_value = scan_results

    repository = Mock()

    assessment_service = Mock()
    assessment_service.assess_file.return_value = assessment_runs

    report_service = Mock()
    report_service.generate_report.return_value = expected_report_path

    # Attach dependencies to a common mock to track execution order.
    workflow_calls = Mock()
    workflow_calls.attach_mock(scan_service, "scan_service")
    workflow_calls.attach_mock(repository, "repository")
    workflow_calls.attach_mock(assessment_service, "assessment_service")
    workflow_calls.attach_mock(report_service, "report_service")

    service = WorkflowService(
        scan_service=scan_service,
        assessment_service=assessment_service,
        report_service=report_service,
        repository=repository,
    )

    result = service.execute(request)

    expected_report_request = ReportRequest(
        input_path=request.output_paths.assessment,
        output_path=request.output_paths.report,
        author=request.author,
        organization=request.organization,
        report_format="markdown",
    )

    assert result == WorkflowResult(
        scan_results=tuple(scan_results),
        assessment_runs=tuple(assessment_runs),
        report_path=expected_report_path,
    )

    # Verify the complete execution sequence.
    assert workflow_calls.mock_calls == [
        call.scan_service.scan_many(
            targets=request.targets,
            port=request.port,
        ),
        call.repository.save_json(
            path=request.output_paths.evidence,
            data=scan_results,
        ),
        call.assessment_service.assess_file(
            input_path=request.output_paths.evidence,
            output_path=request.output_paths.assessment,
            policy_ids=request.policy_ids,
        ),
        call.report_service.generate_report(
            request=expected_report_request,
        ),
    ]


@pytest.mark.parametrize(
    "failure_stage",
    [
        "scan",
        "evidence_persistence",
        "assessment",
        "report",
    ],
)
def test_execute_stops_when_workflow_stage_fails(
    tmp_path,
    tls_scan_factory,
    assessment_run_factory,
    failure_stage,
):
    """Verify that workflow failures prevent subsequent stages."""

    request = make_workflow_request(tmp_path)

    scan_service = Mock()
    scan_service.scan_many.return_value = [
        tls_scan_factory(),
    ]

    repository = Mock()

    assessment_service = Mock()
    assessment_service.assess_file.return_value = [
        assessment_run_factory(),
    ]

    report_service = Mock()
    report_service.generate_report.return_value = request.output_paths.report

    failure = RuntimeError(f"{failure_stage} failed")

    # Inject a failure into the selected workflow stage.
    if failure_stage == "scan":
        scan_service.scan_many.side_effect = failure

    elif failure_stage == "evidence_persistence":
        repository.save_json.side_effect = failure

    elif failure_stage == "assessment":
        assessment_service.assess_file.side_effect = failure

    elif failure_stage == "report":
        report_service.generate_report.side_effect = failure

    service = WorkflowService(
        scan_service=scan_service,
        assessment_service=assessment_service,
        report_service=report_service,
        repository=repository,
    )

    with pytest.raises(RuntimeError, match=f"{failure_stage} failed"):
        service.execute(request)

    # Verify that execution stops at the failing stage.
    assert scan_service.scan_many.call_count == 1

    assert repository.save_json.call_count == (0 if failure_stage == "scan" else 1)

    assert assessment_service.assess_file.call_count == (
        1 if failure_stage in {"assessment", "report"} else 0
    )

    assert report_service.generate_report.call_count == (
        1 if failure_stage == "report" else 0
    )
