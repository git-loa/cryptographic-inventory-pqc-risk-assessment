"""Unit tests for the report command."""

import argparse
from pathlib import Path
from unittest.mock import Mock

import pytest

import pqc_inventory.commands.report as report_command
from pqc_inventory.application.report_request import (
    BatchReportRequest,
    ReportRequest,
)
from pqc_inventory.commands.constants import (
    EXIT_CANCELLED,
    EXIT_ERROR,
    EXIT_INVALID_INPUT,
    EXIT_SUCCESS,
)
from pqc_inventory.storage.json_repository import JSONRepositoryError


def make_args(
    workspace: Path,
    *,
    input_path: str = "assessments/results.json",
    output: str | None = None,
    output_dir: str | None = None,
    report_format: str = "markdown",
    all_formats: bool = False,
) -> argparse.Namespace:
    """Create report command arguments for testing."""

    return argparse.Namespace(
        input=input_path,
        output=output,
        output_dir=output_dir,
        format=report_format,
        all_formats=all_formats,
        author="Test Author",
        organization="Test Organization",
        workspace=Mock(reports_dir=workspace),
    )


# ============================================================
# Parser registration
# ============================================================


def test_register_parser_defaults():
    """Verify report parser defaults."""

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    report_command.register_parser(subparsers)

    args = parser.parse_args(["report", "--input", "results.json"])

    assert args.command == "report"
    assert args.input == "results.json"
    assert args.output is None
    assert args.output_dir is None
    assert args.format is None
    assert args.all_formats is False
    assert args.author == "Unknown Author"
    assert args.organization == "Independent Research"


def test_register_parser_accepts_all_formats():
    """Verify the parser accepts batch report generation."""

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    report_command.register_parser(subparsers)

    args = parser.parse_args(["report", "--input", "results.json", "--all-formats"])

    assert args.all_formats is True


def test_register_parser_rejects_format_and_all_formats_together():
    """Verify single-format and batch options are mutually exclusive."""

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    report_command.register_parser(subparsers)

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "report",
                "--input",
                "results.json",
                "--format",
                "markdown",
                "--all-formats",
            ]
        )


# ============================================================
# Single-format report generation
# ============================================================


def test_run_report_success_uses_workspace_default(
    monkeypatch,
    tmp_path,
):
    """Verify successful generation using the workspace default."""

    args = make_args(tmp_path)

    expected_output = tmp_path / "assessment_report.md"
    generated_path = expected_output

    mock_service = Mock()
    mock_service.generate_report.return_value = generated_path

    mock_resolver = Mock(return_value=expected_output)

    monkeypatch.setattr(
        report_command,
        "resolve_output_path",
        mock_resolver,
    )
    monkeypatch.setattr(
        report_command,
        "ReportService",
        Mock(return_value=mock_service),
    )

    result = report_command.run_report(args)

    assert result == EXIT_SUCCESS

    mock_resolver.assert_called_once_with(
        output_path=expected_output,
        allowed_extensions={".md"},
    )

    mock_service.generate_report.assert_called_once_with(
        ReportRequest(
            input_path=Path(args.input),
            output_path=expected_output,
            author=args.author,
            organization=args.organization,
            report_format=args.format,
        )
    )


def test_run_report_success_uses_explicit_output(
    monkeypatch,
    tmp_path,
):
    """Verify an explicit output path overrides the workspace default."""

    explicit_output = tmp_path / "custom_report.md"
    args = make_args(tmp_path, output=str(explicit_output))

    mock_service = Mock()
    mock_service.generate_report.return_value = explicit_output

    mock_resolver = Mock(return_value=explicit_output)

    monkeypatch.setattr(
        report_command,
        "resolve_output_path",
        mock_resolver,
    )
    monkeypatch.setattr(
        report_command,
        "ReportService",
        Mock(return_value=mock_service),
    )

    result = report_command.run_report(args)

    assert result == EXIT_SUCCESS

    mock_resolver.assert_called_once_with(
        output_path=str(explicit_output),
        allowed_extensions={".md"},
    )


def test_run_report_output_cancelled(monkeypatch, tmp_path, capsys):
    """Verify cancellation prevents report generation."""

    args = make_args(tmp_path)

    mock_service = Mock()

    monkeypatch.setattr(
        report_command,
        "resolve_output_path",
        Mock(return_value=None),
    )
    monkeypatch.setattr(
        report_command,
        "ReportService",
        Mock(return_value=mock_service),
    )

    result = report_command.run_report(args)

    assert result == EXIT_CANCELLED
    assert "Report generation cancelled" in capsys.readouterr().out

    mock_service.generate_report.assert_not_called()


def test_run_report_keyboard_interrupt(monkeypatch, tmp_path, capsys):
    """Verify keyboard interruption cancels report generation."""

    args = make_args(tmp_path)

    mock_service = Mock()

    def raise_interrupt(**kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(
        report_command,
        "resolve_output_path",
        raise_interrupt,
    )
    monkeypatch.setattr(
        report_command,
        "ReportService",
        Mock(return_value=mock_service),
    )

    result = report_command.run_report(args)

    assert result == EXIT_CANCELLED
    assert "Report generation cancelled" in capsys.readouterr().out

    mock_service.generate_report.assert_not_called()


def test_run_report_eoferror(monkeypatch, tmp_path, capsys):
    """Verify EOF while resolving output cancels report generation."""

    args = make_args(tmp_path)

    mock_service = Mock()

    def raise_eoferror(**kwargs):
        raise EOFError

    monkeypatch.setattr(
        report_command,
        "resolve_output_path",
        raise_eoferror,
    )
    monkeypatch.setattr(
        report_command,
        "ReportService",
        Mock(return_value=mock_service),
    )

    result = report_command.run_report(args)

    assert result == EXIT_CANCELLED
    assert "Report generation cancelled" in capsys.readouterr().out

    mock_service.generate_report.assert_not_called()


# ============================================================
# Batch report generation
# ============================================================


def test_run_report_batch_success(monkeypatch, tmp_path):
    """Verify successful generation of all registered formats."""

    args = make_args(tmp_path, all_formats=True)

    generated_paths = [
        tmp_path / "assessment_report.md",
    ]

    mock_service = Mock()
    mock_service.renderers = {"markdown": Mock()}
    mock_service.generate_all_reports.return_value = generated_paths

    monkeypatch.setattr(
        report_command,
        "ReportService",
        Mock(return_value=mock_service),
    )

    result = report_command.run_report(args)

    assert result == EXIT_SUCCESS

    mock_service.generate_all_reports.assert_called_once_with(
        BatchReportRequest(
            input_path=Path(args.input),
            output_directory=tmp_path,
            author=args.author,
            organization=args.organization,
        )
    )


def test_run_report_batch_uses_explicit_output_directory(
    monkeypatch,
    tmp_path,
):
    """Verify batch generation uses the supplied output directory."""

    output_directory = tmp_path / "custom_reports"
    args = make_args(
        tmp_path,
        output_dir=str(output_directory),
        all_formats=True,
    )

    mock_service = Mock()
    mock_service.renderers = {"markdown": Mock()}
    mock_service.generate_all_reports.return_value = []

    monkeypatch.setattr(
        report_command,
        "ReportService",
        Mock(return_value=mock_service),
    )

    result = report_command.run_report(args)

    assert result == EXIT_SUCCESS

    request = mock_service.generate_all_reports.call_args.args[0]

    assert request.output_directory == output_directory


def test_run_report_batch_overwrite_declined(
    monkeypatch,
    tmp_path,
    capsys,
):
    """Verify declining batch overwrite prevents report generation."""

    args = make_args(tmp_path, all_formats=True)

    existing_report = tmp_path / "assessment_report.md"
    existing_report.write_text("Existing report", encoding="utf-8")

    mock_service = Mock()
    mock_service.renderers = {"markdown": Mock()}

    monkeypatch.setattr(
        report_command,
        "ReportService",
        Mock(return_value=mock_service),
    )
    monkeypatch.setattr(
        "builtins.input",
        Mock(return_value="n"),
    )

    result = report_command.run_report(args)

    assert result == EXIT_CANCELLED
    assert "cancelled" in capsys.readouterr().out.lower()

    mock_service.generate_all_reports.assert_not_called()

    assert existing_report.read_text(encoding="utf-8") == "Existing report"


def test_run_report_batch_overwrite_confirmed(
    monkeypatch,
    tmp_path,
):
    """Verify batch generation proceeds after overwrite confirmation."""

    args = make_args(tmp_path, all_formats=True)

    existing_report = tmp_path / "assessment_report.md"
    existing_report.write_text("Existing report", encoding="utf-8")

    mock_service = Mock()
    mock_service.renderers = {"markdown": Mock()}
    mock_service.generate_all_reports.return_value = [existing_report]

    monkeypatch.setattr(
        report_command,
        "ReportService",
        Mock(return_value=mock_service),
    )
    monkeypatch.setattr(
        "builtins.input",
        Mock(return_value="y"),
    )

    result = report_command.run_report(args)

    assert result == EXIT_SUCCESS
    mock_service.generate_all_reports.assert_called_once()


def test_run_report_batch_keyboard_interrupt(
    monkeypatch,
    tmp_path,
    capsys,
):
    """Verify interruption during batch confirmation cancels generation."""

    args = make_args(tmp_path, all_formats=True)

    existing_report = tmp_path / "assessment_report.md"
    existing_report.write_text("Existing report", encoding="utf-8")

    mock_service = Mock()
    mock_service.renderers = {"markdown": Mock()}

    def raise_interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(
        report_command,
        "ReportService",
        Mock(return_value=mock_service),
    )
    monkeypatch.setattr(
        "builtins.input",
        raise_interrupt,
    )

    result = report_command.run_report(args)

    assert result == EXIT_CANCELLED
    assert "Report generation cancelled" in capsys.readouterr().out

    mock_service.generate_all_reports.assert_not_called()


# ============================================================
# Error handling
# ============================================================


@pytest.mark.parametrize(
    ("exception", "expected_exit_code", "message"),
    [
        (
            ValueError("Invalid assessment data."),
            EXIT_INVALID_INPUT,
            "Report input error",
        ),
        (
            JSONRepositoryError("Unable to load assessment results."),
            EXIT_ERROR,
            "Report data error",
        ),
        (
            OSError("Permission denied."),
            EXIT_ERROR,
            "Report output error",
        ),
    ],
)
def test_run_report_handles_generation_errors(
    monkeypatch,
    tmp_path,
    capsys,
    exception,
    expected_exit_code,
    message,
):
    """Verify report generation errors produce the appropriate exit code."""

    args = make_args(tmp_path)

    mock_service = Mock()
    mock_service.generate_report.side_effect = exception

    monkeypatch.setattr(
        report_command,
        "resolve_output_path",
        Mock(return_value=tmp_path / "assessment_report.md"),
    )
    monkeypatch.setattr(
        report_command,
        "ReportService",
        Mock(return_value=mock_service),
    )

    result = report_command.run_report(args)

    assert result == expected_exit_code
    assert message in capsys.readouterr().err


@pytest.mark.parametrize(
    ("exception", "expected_exit_code", "message"),
    [
        (
            ValueError("Invalid assessment data."),
            EXIT_INVALID_INPUT,
            "Report input error",
        ),
        (
            JSONRepositoryError("Unable to load assessment results."),
            EXIT_ERROR,
            "Report data error",
        ),
        (
            OSError("Unable to write reports."),
            EXIT_ERROR,
            "Report output error",
        ),
    ],
)
def test_run_report_handles_batch_errors(
    monkeypatch,
    tmp_path,
    capsys,
    exception,
    expected_exit_code,
    message,
):
    """Verify batch generation errors produce the appropriate exit code."""

    args = make_args(tmp_path, all_formats=True)

    mock_service = Mock()
    mock_service.renderers = {"markdown": Mock()}
    mock_service.generate_all_reports.side_effect = exception

    monkeypatch.setattr(
        report_command,
        "ReportService",
        Mock(return_value=mock_service),
    )

    result = report_command.run_report(args)

    assert result == expected_exit_code
    assert message in capsys.readouterr().err


def test_run_report_does_not_suppress_unexpected_errors(
    monkeypatch,
    tmp_path,
):
    args = make_args(tmp_path)

    mock_service = Mock()
    mock_service.generate_report.side_effect = RuntimeError(
        "Unexpected programming error"
    )

    monkeypatch.setattr(
        report_command,
        "ReportService",
        Mock(return_value=mock_service),
    )

    with pytest.raises(
        RuntimeError,
        match="Unexpected programming error",
    ):
        report_command.run_report(args)


def test_run_report_does_not_suppress_unexpected_batch_errors(
    monkeypatch,
    tmp_path,
):
    args = make_args(tmp_path, all_formats=True)

    mock_service = Mock()
    mock_service.renderers = {"markdown": Mock()}
    mock_service.generate_all_reports.side_effect = RuntimeError(
        "Unexpected batch failure."
    )

    monkeypatch.setattr(
        report_command,
        "ReportService",
        Mock(return_value=mock_service),
    )

    with pytest.raises(
        RuntimeError,
        match="Unexpected batch failure",
    ):
        report_command.run_report(args)
