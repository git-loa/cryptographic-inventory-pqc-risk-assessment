"""Tests for assessment report generation services."""

from unittest.mock import Mock

import pytest

from pqc_inventory.application.report_request import (
    BatchReportRequest,
    ReportRequest,
)
from pqc_inventory.application.report_service import ReportService


def test_generate_report_successfully(
    tmp_path,
    assessment_run_factory,
    policy_execution_record_factory,
    finding_factory,
):
    """Verify that a report is loaded, rendered, and saved successfully."""

    assessment_run = assessment_run_factory(
        assessments={
            "A1": policy_execution_record_factory(
                findings=[finding_factory()],
            )
        }
    )

    repository = Mock()
    repository.load_json.return_value = [assessment_run]

    renderer = Mock()
    renderer.render.return_value = "# Assessment Report"

    service = ReportService(
        repository=repository,
        renderers={"markdown": renderer},
    )

    input_path = tmp_path / "assessment.json"
    output_path = tmp_path / "reports" / "assessment_report.md"

    request = ReportRequest(
        input_path=input_path,
        output_path=output_path,
        author="Test Author",
        organization="Test Organization",
        report_format="markdown",
    )

    generated_path = service.generate_report(request)

    assert generated_path == output_path
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == "# Assessment Report"

    repository.load_json.assert_called_once_with(input_path)
    renderer.render.assert_called_once()


def test_generate_report_rejects_unsupported_format(tmp_path):
    """Verify that unsupported formats are rejected before loading data."""

    repository = Mock()
    renderer = Mock()

    service = ReportService(
        repository=repository,
        renderers={"markdown": renderer},
    )

    request = ReportRequest(
        input_path=tmp_path / "assessment.json",
        output_path=tmp_path / "assessment_report.pdf",
        author="Test Author",
        organization="Test Organization",
        report_format="pdf",
    )

    with pytest.raises(ValueError, match="Unsupported report format: pdf"):
        service.generate_report(request)

    repository.load_json.assert_not_called()
    renderer.render.assert_not_called()


def test_generate_report_rejects_invalid_assessment_data(tmp_path):
    """Verify that invalid assessment data prevents report generation."""

    repository = Mock()
    repository.load_json.return_value = {"invalid": "assessment"}

    renderer = Mock()

    service = ReportService(
        repository=repository,
        renderers={"markdown": renderer},
    )

    request = ReportRequest(
        input_path=tmp_path / "assessment.json",
        output_path=tmp_path / "assessment_report.md",
        author="Test Author",
        organization="Test Organization",
        report_format="markdown",
    )

    with pytest.raises(ValueError, match="missing required fields"):
        service.generate_report(request)

    repository.load_json.assert_called_once()
    renderer.render.assert_not_called()


def test_generate_all_reports_successfully(
    tmp_path,
    assessment_run_factory,
    policy_execution_record_factory,
    finding_factory,
):
    """Verify that all registered report formats are generated."""

    assessment_run = assessment_run_factory(
        assessments={
            "A1": policy_execution_record_factory(
                findings=[finding_factory()],
            )
        }
    )

    repository = Mock()
    repository.load_json.return_value = [assessment_run]

    markdown_renderer = Mock()
    markdown_renderer.render.return_value = "# Markdown Report"

    html_renderer = Mock()
    html_renderer.render.return_value = "<h1>HTML Report</h1>"

    service = ReportService(
        repository=repository,
        renderers={
            "markdown": markdown_renderer,
            "html": html_renderer,
        },
    )

    input_path = tmp_path / "assessment.json"
    output_directory = tmp_path / "reports"

    request = BatchReportRequest(
        input_path=input_path,
        output_directory=output_directory,
        author="Test Author",
        organization="Test Organization",
    )

    generated_reports = service.generate_all_reports(request)

    expected_markdown = output_directory / "assessment_report.md"
    expected_html = output_directory / "assessment_report.html"

    assert generated_reports == [
        expected_markdown,
        expected_html,
    ]

    assert expected_markdown.read_text(encoding="utf-8") == "# Markdown Report"
    assert expected_html.read_text(encoding="utf-8") == "<h1>HTML Report</h1>"

    repository.load_json.assert_called_once_with(input_path)
    markdown_renderer.render.assert_called_once()
    html_renderer.render.assert_called_once()


def test_generate_all_reports_builds_report_data_once(
    tmp_path,
    assessment_run_factory,
):
    """Verify that batch generation shares one ReportData instance."""

    assessment_run = assessment_run_factory()

    repository = Mock()
    repository.load_json.return_value = [assessment_run]

    markdown_renderer = Mock()
    markdown_renderer.render.return_value = "# Markdown Report"

    html_renderer = Mock()
    html_renderer.render.return_value = "<h1>HTML Report</h1>"

    service = ReportService(
        repository=repository,
        renderers={
            "markdown": markdown_renderer,
            "html": html_renderer,
        },
    )

    request = BatchReportRequest(
        input_path=tmp_path / "assessment.json",
        output_directory=tmp_path / "reports",
        author="Test Author",
        organization="Test Organization",
    )

    service.generate_all_reports(request)

    markdown_data = markdown_renderer.render.call_args.kwargs["report_data"]
    html_data = html_renderer.render.call_args.kwargs["report_data"]

    assert markdown_data is html_data
    repository.load_json.assert_called_once()
