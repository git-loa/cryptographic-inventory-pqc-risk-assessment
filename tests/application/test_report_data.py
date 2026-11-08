"""Unit tests for the report data aggregation logic."""

from pqc_inventory.application.report_data import ReportDataBuilder


def test_build_overview_with_no_assessment_runs():
    """Test overview generation when no assessment runs are supplied."""

    builder = ReportDataBuilder(assessment_runs=[])
    overview = builder.build_overview()

    assert overview["total_assessment_runs"] == 0
    assert overview["methodology_versions"] == []
    assert overview["policies_executed"] == []

    assert overview["policy_execution_counts"] == {
        "completed": 0,
        "partial": 0,
        "failed": 0,
        "not_assessed": 0,
    }

    assert overview["scan_status_counts"] == {
        "completed": 0,
        "partial": 0,
        "failed": 0,
    }

    assert overview["classification_counts"] == {
        "acceptable": 0,
        "acceptable_with_review": 0,
        "unacceptable": 0,
        "unknown": 0,
    }


def test_build_overview_with_multiple_assessment_runs(
    assessment_run_factory,
    policy_execution_record_factory,
):
    """Test aggregation of multiple assessment runs."""

    assessment_runs = [
        assessment_run_factory(
            assessment_run_id="run-001",
            methodology_version="1.0",
            assessments={
                "A1": policy_execution_record_factory(policy_id="A1"),
            },
        ),
        assessment_run_factory(
            assessment_run_id="run-002",
            methodology_version="1.1",
            domain="example.org",
            assessments={
                "A1": policy_execution_record_factory(policy_id="A1"),
                "A2": policy_execution_record_factory(
                    policy_id="A2",
                    execution_status="failed",
                ),
            },
        ),
    ]

    builder = ReportDataBuilder(assessment_runs)
    overview = builder.build_overview()

    assert overview["total_assessment_runs"] == 2
    assert overview["methodology_versions"] == ["1.0", "1.1"]
    assert overview["policies_executed"] == ["A1", "A2"]


def test_build_overview_counts_policy_execution_statuses(
    assessment_run_factory,
    policy_execution_record_factory,
):
    """Test policy execution status aggregation across assessment runs."""

    assessment_runs = [
        assessment_run_factory(
            assessment_run_id="run-001",
            assessments={
                "A1": policy_execution_record_factory(policy_id="A1"),
                "A2": policy_execution_record_factory(
                    policy_id="A2",
                    execution_status="failed",
                ),
            },
        ),
        assessment_run_factory(
            assessment_run_id="run-002",
            assessments={
                "A1": policy_execution_record_factory(policy_id="A1"),
                "A2": policy_execution_record_factory(
                    policy_id="A2",
                    execution_status="partial",
                ),
                "A3": policy_execution_record_factory(
                    policy_id="A3",
                    execution_status="not_assessed",
                ),
            },
        ),
    ]

    builder = ReportDataBuilder(assessment_runs)
    overview = builder.build_overview()

    assert overview["policy_execution_counts"] == {
        "completed": 2,
        "partial": 1,
        "failed": 1,
        "not_assessed": 1,
    }


def test_build_overview_counts_scan_statuses(assessment_run_factory):
    """Test TLS scan-status aggregation across assessment runs."""

    assessment_runs = [
        assessment_run_factory(
            assessment_run_id="run-001",
            scan_status="completed",
        ),
        assessment_run_factory(
            assessment_run_id="run-002",
            scan_status="partial",
        ),
        assessment_run_factory(
            assessment_run_id="run-003",
            scan_status="failed",
        ),
        assessment_run_factory(
            assessment_run_id="run-004",
            scan_status="completed",
        ),
    ]

    builder = ReportDataBuilder(assessment_runs)
    overview = builder.build_overview()

    assert overview["scan_status_counts"] == {
        "completed": 2,
        "partial": 1,
        "failed": 1,
    }


def test_build_overview_counts_finding_classifications(
    assessment_run_factory,
    policy_execution_record_factory,
    finding_factory,
):
    """Test finding classification aggregation across assessment runs."""

    findings = [
        finding_factory(finding_id="finding-001"),
        finding_factory(
            finding_id="finding-002",
            classification="acceptable_with_review",
        ),
        finding_factory(
            finding_id="finding-003",
            classification="unacceptable",
        ),
        finding_factory(
            finding_id="finding-004",
            classification="unknown",
        ),
    ]

    assessment_runs = [
        assessment_run_factory(
            assessment_run_id="run-001",
            assessments={
                "A1": policy_execution_record_factory(
                    policy_id="A1",
                    findings=findings[:2],
                ),
            },
        ),
        assessment_run_factory(
            assessment_run_id="run-002",
            assessments={
                "A1": policy_execution_record_factory(
                    policy_id="A1",
                    findings=findings[2:],
                ),
            },
        ),
    ]

    builder = ReportDataBuilder(assessment_runs)
    overview = builder.build_overview()

    assert overview["classification_counts"] == {
        "acceptable": 1,
        "acceptable_with_review": 1,
        "unacceptable": 1,
        "unknown": 1,
    }


def test_failed_policy_without_findings(
    assessment_run_factory,
    policy_execution_record_factory,
):
    """Ensure failed policies count as failures without affecting classifications."""

    assessment_runs = [
        assessment_run_factory(
            assessment_run_id="run-001",
            assessments={
                "A1": policy_execution_record_factory(
                    policy_id="A1",
                    execution_status="failed",
                ),
            },
        ),
    ]

    builder = ReportDataBuilder(assessment_runs)
    overview = builder.build_overview()

    assert overview["policy_execution_counts"]["failed"] == 1

    assert overview["classification_counts"] == {
        "acceptable": 0,
        "acceptable_with_review": 0,
        "unacceptable": 0,
        "unknown": 0,
    }


def test_build_overview_counts_multiple_findings_per_policy(
    assessment_run_factory,
    policy_execution_record_factory,
    finding_factory,
):
    """Ensure every finding is counted individually."""

    findings = [
        finding_factory(
            finding_id="finding-001",
            classification="acceptable",
        ),
        finding_factory(
            finding_id="finding-002",
            classification="acceptable",
        ),
        finding_factory(
            finding_id="finding-003",
            classification="unacceptable",
        ),
    ]

    assessment_runs = [
        assessment_run_factory(
            assessment_run_id="run-001",
            assessments={
                "A1": policy_execution_record_factory(
                    policy_id="A1",
                    findings=findings,
                ),
            },
        ),
    ]

    builder = ReportDataBuilder(assessment_runs)
    overview = builder.build_overview()

    assert overview["classification_counts"] == {
        "acceptable": 2,
        "acceptable_with_review": 0,
        "unacceptable": 1,
        "unknown": 0,
    }


def test_build_complete_report_data(
    assessment_run_factory,
):
    """Ensure the builder assembles all report data sections."""

    assessment_runs = [
        assessment_run_factory(
            assessment_run_id="run-001",
            methodology_version="1.0",
        ),
    ]

    metadata = {
        "report_title": "TLS Cryptographic Assessment Report",
        "report_id": "report-001",
        "generated_at": "2026-11-03T12:00:00Z",
        "author": "Security Assessment Team",
        "organization": "Example Organization",
        "report_version": "1.0",
    }

    builder = ReportDataBuilder(assessment_runs)
    report_data = builder.build_report_data(metadata)

    assert report_data["metadata"] == metadata
    assert report_data["assessment_runs"] == assessment_runs

    assert report_data["overview"]["total_assessment_runs"] == 1
    assert report_data["overview"]["methodology_versions"] == ["1.0"]


def test_build_report_data_without_assessment_runs():
    """Ensure complete report data can be built from an empty collection."""

    metadata = {
        "report_title": "TLS Cryptographic Assessment Report",
        "report_id": "report-002",
        "generated_at": "2026-11-03T12:00:00Z",
        "author": "Security Assessment Team",
        "organization": "Example Organization",
        "report_version": "1.0",
    }

    builder = ReportDataBuilder([])
    report_data = builder.build_report_data(metadata)

    assert report_data["metadata"] == metadata
    assert report_data["assessment_runs"] == []
    assert report_data["overview"]["total_assessment_runs"] == 0
    assert report_data["overview"]["methodology_versions"] == []
