"""CLI command for generating assessment reports."""

import argparse
import sys
from pathlib import Path

from pqc_inventory.application.report_request import (
    BatchReportRequest,
    ReportRequest,
)
from pqc_inventory.application.report_service import (
    REPORT_FILENAMES,
    ReportService,
)
from pqc_inventory.commands.common import (
    resolve_output_path,
    resolve_output_directory,
)
from pqc_inventory.commands.constants import (
    EXIT_CANCELLED,
    EXIT_ERROR,
    EXIT_INVALID_INPUT,
    EXIT_SUCCESS,
)
from pqc_inventory.storage.json_repository import JSONRepositoryError


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the report command and its arguments."""

    report_parser = subparsers.add_parser(
        "report",
        help="Generate reports from assessment results.",
        description="Render saved assessment results into reports.",
    )

    report_parser.add_argument(
        "--input",
        required=True,
        help="Path to the saved assessment results JSON file.",
    )

    report_parser.add_argument(
        "--output",
        default=None,
        help=(
            "Destination path for a single report "
            "(default: workspace reports directory)."
        ),
    )

    report_parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Destination directory for batch reports "
            "(default: workspace reports directory)."
        ),
    )

    format_group = report_parser.add_mutually_exclusive_group()

    format_group.add_argument(
        "--format",
        choices=["markdown"],
        default=None,
        help="Generate a report in the specified format (default: markdown).",
    )

    format_group.add_argument(
        "--all-formats",
        action="store_true",
        help="Generate reports in all registered formats.",
    )

    report_parser.add_argument(
        "--author",
        default="Unknown Author",
        help="Report author (default: Unknown Author).",
    )

    report_parser.add_argument(
        "--organization",
        default="Independent Research",
        help="Organization associated with the report.",
    )


def confirm_batch_overwrite(
    output_directory: Path,
    service: ReportService,
) -> bool:
    """Ask the user to confirm overwriting existing reports."""

    existing_reports = [
        output_directory / REPORT_FILENAMES[report_format]
        for report_format in service.renderers
        if report_format in REPORT_FILENAMES
        and (output_directory / REPORT_FILENAMES[report_format]).exists()
    ]

    if not existing_reports:
        return True

    print("\nThe following reports already exist:")
    for report_path in existing_reports:
        print(f"  {report_path}")

    confirmation = input("\nOverwrite all existing reports? [y/N]: ").strip().lower()

    return confirmation == "y"


def generate_batch_report(
    args: argparse.Namespace,
    service: ReportService,
) -> int:
    """Generate reports in all registered formats."""

    proposed_directory = (
        args.output_dir if args.output_dir is not None else args.workspace.reports_dir
    )

    output_directory = resolve_output_directory(
        output_directory=proposed_directory,
    )

    if output_directory is None:
        print("Report generation cancelled by user.")
        return EXIT_CANCELLED

    if not confirm_batch_overwrite(output_directory, service):
        print("Report generation cancelled by user.")
        return EXIT_CANCELLED

    request = BatchReportRequest(
        input_path=Path(args.input),
        output_directory=output_directory,
        author=args.author,
        organization=args.organization,
    )

    generated_paths = service.generate_all_reports(request)

    print("\nReports generated successfully.")
    for generated_path in generated_paths:
        print(f"  {generated_path}")

    return EXIT_SUCCESS


def generate_single_report(
    args: argparse.Namespace,
    service: ReportService,
) -> int:
    """Generate a report in the requested format."""

    default_output = args.workspace.reports_dir / "assessment_report.md"

    output_path = resolve_output_path(
        output_path=args.output or default_output,
        allowed_extensions={".md"},
    )

    if output_path is None:
        print("Report generation cancelled by user.")
        return EXIT_CANCELLED

    request = ReportRequest(
        input_path=Path(args.input),
        output_path=output_path,
        author=args.author,
        organization=args.organization,
        report_format=args.format or "markdown",
    )

    generated_path = service.generate_report(request)

    print("\nReport generated successfully.")
    print(f"Report saved to: {generated_path}")

    return EXIT_SUCCESS


def run_report(args: argparse.Namespace) -> int:
    """Generate assessment reports and report the operation's outcome."""

    exit_code = EXIT_SUCCESS

    try:
        service = ReportService()

        generate = generate_batch_report if args.all_formats else generate_single_report

        exit_code = generate(args, service)

    except (EOFError, KeyboardInterrupt):
        print("\nReport generation cancelled by user.")
        exit_code = EXIT_CANCELLED

    except ValueError as exc:
        print(f"Report input error: {exc}", file=sys.stderr)
        exit_code = EXIT_INVALID_INPUT

    except JSONRepositoryError as exc:
        print(f"Report data error: {exc}", file=sys.stderr)
        exit_code = EXIT_ERROR

    except OSError as exc:
        print(f"Report output error: {exc}", file=sys.stderr)
        exit_code = EXIT_ERROR

    return exit_code
