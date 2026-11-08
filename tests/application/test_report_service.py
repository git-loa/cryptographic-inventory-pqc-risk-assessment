"""Tests for assessment report generation services."""

from unittest.mock import Mock

import pytest

from pqc_inventory.application.report_request import (
    BatchReportRequest,
    ReportRequest,
)
from pqc_inventory.application.report_service import ReportService


def create_symlink_or_skip(link_path, target_path):
    """Create a symbolic link or skip when the OS does not permit it."""

    try:
        link_path.symlink_to(target_path)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symbolic links are unavailable: {exc}")


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


def test_generate_report_rejects_symlink_destination(
    tmp_path,
    assessment_run_factory,
):
    """Verify that single-report generation rejects symbolic links."""

    repository = Mock()
    repository.load_json.return_value = [assessment_run_factory()]

    renderer = Mock()
    renderer.render.return_value = "# Assessment Report"

    service = ReportService(
        repository=repository,
        renderers={"markdown": renderer},
    )

    target_path = tmp_path / "protected.txt"
    target_path.write_text("Original content", encoding="utf-8")

    output_path = tmp_path / "reports" / "assessment_report.md"
    output_path.parent.mkdir()

    create_symlink_or_skip(output_path, target_path)

    request = ReportRequest(
        input_path=tmp_path / "assessment.json",
        output_path=output_path,
        author="Test Author",
        organization="Test Organization",
    )

    with pytest.raises(ValueError, match="symbolic link"):
        service.generate_report(request)

    assert target_path.read_text(encoding="utf-8") == "Original content"


def test_generate_all_reports_rejects_symlink_destination(
    tmp_path,
    assessment_run_factory,
):
    """Verify that batch generation rejects symbolic-link destinations."""

    repository = Mock()
    repository.load_json.return_value = [assessment_run_factory()]

    renderer = Mock()
    renderer.render.return_value = "# Assessment Report"

    service = ReportService(
        repository=repository,
        renderers={"markdown": renderer},
    )

    output_directory = tmp_path / "reports"
    output_directory.mkdir()

    target_path = tmp_path / "protected.txt"
    target_path.write_text("Original content", encoding="utf-8")

    output_path = output_directory / "assessment_report.md"

    create_symlink_or_skip(output_path, target_path)

    request = BatchReportRequest(
        input_path=tmp_path / "assessment.json",
        output_directory=output_directory,
        author="Test Author",
        organization="Test Organization",
    )

    with pytest.raises(ValueError, match="symbolic link"):
        service.generate_all_reports(request)

    assert target_path.read_text(encoding="utf-8") == "Original content"


def test_generate_report_rejects_symlink_in_parent_directory(
    tmp_path,
    assessment_run_factory,
):
    """Verify that report generation rejects a symlink in a parent directory."""

    target_directory = tmp_path / "real_reports"
    target_directory.mkdir()

    symlink_directory = tmp_path / "reports_link"

    try:
        symlink_directory.symlink_to(
            target_directory,
            target_is_directory=True,
        )
    except OSError as exc:
        pytest.skip(f"Cannot create directory symlink: {exc}")

    repository = Mock()
    repository.load_json.return_value = [assessment_run_factory()]

    renderer = Mock()
    renderer.render.return_value = "# Assessment Report"

    service = ReportService(
        repository=repository,
        renderers={"markdown": renderer},
    )

    output_path = symlink_directory / "assessment_report.md"

    request = ReportRequest(
        input_path=tmp_path / "assessment.json",
        output_path=output_path,
        author="Test Author",
        organization="Test Organization",
        report_format="markdown",
    )

    with pytest.raises(ValueError, match="symbolic links"):
        service.generate_report(request)

    assert not (target_directory / "assessment_report.md").exists()


def test_generate_all_reports_rejects_symlink_output_directory(
    tmp_path,
    assessment_run_factory,
):
    """Verify that batch generation rejects a symlink output directory."""

    target_directory = tmp_path / "real_reports"
    target_directory.mkdir()

    symlink_directory = tmp_path / "reports_link"

    try:
        symlink_directory.symlink_to(
            target_directory,
            target_is_directory=True,
        )
    except OSError as exc:
        pytest.skip(f"Cannot create directory symlink: {exc}")

    repository = Mock()
    repository.load_json.return_value = [assessment_run_factory()]

    renderer = Mock()
    renderer.render.return_value = "# Assessment Report"

    service = ReportService(
        repository=repository,
        renderers={"markdown": renderer},
    )

    request = BatchReportRequest(
        input_path=tmp_path / "assessment.json",
        output_directory=symlink_directory,
        author="Test Author",
        organization="Test Organization",
    )

    with pytest.raises(ValueError, match="symbolic links"):
        service.generate_all_reports(request)

    assert not (target_directory / "assessment_report.md").exists()
