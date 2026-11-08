"""CLI command for executing the complete assessment workflow."""

import argparse
import sys
from pathlib import Path

from pqc_inventory.application.report_service import (
    REPORT_FILENAMES,
    ReportService,
)
from pqc_inventory.application.workflow_request import (
    WorkflowOutputPaths,
    WorkflowRequest,
)
from pqc_inventory.application.workflow_service import WorkflowService
from pqc_inventory.commands.assess import (
    resolve_policy_selection,
    summarize_assessment_results,
)
from pqc_inventory.commands.common import (
    resolve_command_output_path,
    resolve_output_directory,
    valid_port,
)
from pqc_inventory.commands.constants import (
    EXIT_CANCELLED,
    EXIT_ERROR,
    EXIT_INVALID_INPUT,
    EXIT_PARTIAL,
    EXIT_SUCCESS,
)
from pqc_inventory.commands.report import confirm_batch_overwrite
from pqc_inventory.commands.scan import (
    collect_targets,
    summarize_scan_results,
)
from pqc_inventory.storage.json_repository import (
    JSONRepository,
    JSONRepositoryError,
)


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the complete workflow command and its arguments."""

    run_parser = subparsers.add_parser(
        "run",
        help="Run the complete TLS assessment workflow.",
        description=(
            "Collect TLS evidence, execute assessment policies, "
            "and generate assessment reports."
        ),
    )

    # TLS targets.
    target_group = run_parser.add_mutually_exclusive_group(required=True)

    target_group.add_argument(
        "--targets",
        nargs="+",
        metavar="TARGET",
        help="One or more domain names or IP addresses to scan.",
    )

    target_group.add_argument(
        "--targets-file",
        metavar="PATH",
        help="Path to a file containing TLS targets.",
    )

    # TLS connection configuration.
    run_parser.add_argument(
        "--port",
        type=valid_port,
        default=443,
        help="TLS endpoint port (default: 443).",
    )

    # Assessment policy selection.
    run_parser.add_argument(
        "--policies",
        nargs="+",
        metavar="POLICY_ID",
        help="Assessment policies to execute (e.g., --policies A1 A2).",
    )

    run_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Execute all registered policies without confirmation.",
    )

    # Intermediate workflow outputs.
    run_parser.add_argument(
        "--evidence-output",
        default=None,
        help="Destination for collected TLS evidence JSON.",
    )

    run_parser.add_argument(
        "--assessment-output",
        default=None,
        help="Destination for assessment results JSON.",
    )

    # Report destinations.
    output_group = run_parser.add_mutually_exclusive_group()

    output_group.add_argument(
        "--output",
        default=None,
        help="Destination file for a single report.",
    )

    output_group.add_argument(
        "--output-dir",
        default=None,
        help="Destination directory when generating all report formats.",
    )

    # Report format selection.
    format_group = run_parser.add_mutually_exclusive_group()

    format_group.add_argument(
        "--format",
        choices=["markdown", "html"],
        default=None,
        help="Report format (default: markdown).",
    )

    format_group.add_argument(
        "--all-formats",
        action="store_true",
        help="Generate reports in all registered formats.",
    )

    run_parser.add_argument(
        "--author",
        default="Unknown Author",
        help="Report author (default: Unknown Author).",
    )

    run_parser.add_argument(
        "--organization",
        default="Independent Research",
        help="Organization associated with the report.",
    )


def resolve_report_destination(
    args: argparse.Namespace,
    report_service: ReportService,
) -> tuple[Path | None, Path | None] | None:
    """Resolve the destination for single-format or batch reporting.

    Returns:
        A tuple containing either a report file or report directory.
        Returns None if the user cancels.

    Raises:
        ValueError: If incompatible output options are supplied.
        EOFError: If input closes during directory validation.
        KeyboardInterrupt: If the operation is interrupted.
    """

    if args.all_formats:
        if args.output is not None:
            raise ValueError(
                "--output cannot be used with --all-formats. "
                "Use --output-dir instead."
            )

        proposed_directory = (
            args.output_dir
            if args.output_dir is not None
            else args.workspace.reports_dir
        )

        output_directory = resolve_output_directory(
            output_directory=proposed_directory,
        )

        if output_directory is None:
            return None

        if not confirm_batch_overwrite(output_directory, report_service):
            return None

        return None, output_directory

    if args.output_dir is not None:
        raise ValueError("--output-dir requires --all-formats.")

    report_format = args.format or "markdown"

    default_output = args.workspace.reports_dir / REPORT_FILENAMES[report_format]

    output_path = resolve_command_output_path(
        output_path=args.output or default_output,
        allowed_extensions={Path(REPORT_FILENAMES[report_format]).suffix},
    )

    if output_path is None:
        return None

    return output_path, None


def resolve_workflow_output_paths(
    args: argparse.Namespace,
    report_service: ReportService,
) -> WorkflowOutputPaths | None:
    """Resolve and validate all workflow artifact destinations."""

    evidence_path = resolve_command_output_path(
        output_path=(
            args.evidence_output or args.workspace.evidence_dir / "tls_scans.json"
        ),
        allowed_extensions={".json"},
    )

    if evidence_path is None:
        return None

    assessment_path = resolve_command_output_path(
        output_path=(
            args.assessment_output
            or args.workspace.assessments_dir / "assessment_runs.json"
        ),
        allowed_extensions={".json"},
    )

    if assessment_path is None:
        return None

    # Prevent assessment output from overwriting collected evidence.
    if evidence_path.resolve() == assessment_path.resolve():
        raise ValueError("Evidence and assessment outputs must use different paths.")

    report_destination = resolve_report_destination(
        args=args,
        report_service=report_service,
    )

    if report_destination is None:
        return None

    report_path, report_directory = report_destination

    return WorkflowOutputPaths(
        evidence=evidence_path,
        assessment=assessment_path,
        report=report_path,
        report_directory=report_directory,
    )


def summarize_workflow(
    result,
    output_paths: WorkflowOutputPaths,
) -> int:
    """Summarize workflow results and determine the exit status."""

    print("\nTLS Collection")
    print("--------------")

    scan_status = summarize_scan_results(
        results=list(result.scan_results),
        output_path=output_paths.evidence,
    )

    print("\nAssessment")
    print("----------")

    assessment_status = summarize_assessment_results(
        results=list(result.assessment_runs),
        output_path=output_paths.assessment,
    )

    print("\nGenerated Reports")
    print("------------------")

    for report_path in result.report_paths:
        print(f"  {report_path}")

    if EXIT_PARTIAL in (scan_status, assessment_status):
        return EXIT_PARTIAL

    return EXIT_SUCCESS


def _build_workflow_request(
    args: argparse.Namespace,
    report_service: ReportService,
) -> tuple[WorkflowRequest | None, int]:
    """Validate CLI inputs and construct the application workflow request."""

    request = None
    status = EXIT_SUCCESS

    # Step 1: Validate targets and resolve policy selection.
    try:
        targets = collect_targets(args)
        selected_policy_ids = resolve_policy_selection(args)

    except (ValueError, OSError) as exc:
        print(f"Workflow input error: {exc}", file=sys.stderr)
        status = EXIT_INVALID_INPUT

    except (EOFError, KeyboardInterrupt):
        print("\nWorkflow cancelled by user.")
        status = EXIT_CANCELLED

    else:
        if selected_policy_ids is None:
            print("Workflow cancelled by user.")
            status = EXIT_CANCELLED

        else:
            # Step 2: Resolve output destinations.
            try:
                output_paths = resolve_workflow_output_paths(
                    args=args,
                    report_service=report_service,
                )

            except ValueError as exc:
                print(f"Workflow output error: {exc}", file=sys.stderr)
                status = EXIT_INVALID_INPUT

            except (EOFError, KeyboardInterrupt):
                print("\nWorkflow cancelled by user.")
                status = EXIT_CANCELLED

            else:
                if output_paths is None:
                    print("Workflow cancelled by user.")
                    status = EXIT_CANCELLED

                else:
                    # Step 3: Construct the application request.
                    request = WorkflowRequest(
                        targets=tuple(targets),
                        output_paths=output_paths,
                        port=args.port,
                        policy_ids=tuple(selected_policy_ids),
                        author=args.author,
                        organization=args.organization,
                        report_format=args.format or "markdown",
                    )

    return request, status


def run_workflow(args: argparse.Namespace) -> int:
    """Execute the complete assessment workflow through the CLI."""

    repository = JSONRepository()
    report_service = ReportService(repository=repository)

    try:
        # Step 1: Prepare the application request.
        request, preparation_status = _build_workflow_request(
            args=args,
            report_service=report_service,
        )

        if request is None:
            return preparation_status

        # Step 2: Execute the application workflow.
        service = WorkflowService(
            repository=repository,
            report_service=report_service,
        )

        result = service.execute(request)

    except (ValueError, KeyError) as exc:
        print(f"Workflow execution error: {exc}", file=sys.stderr)
        return EXIT_INVALID_INPUT

    except (JSONRepositoryError, OSError) as exc:
        print(f"Workflow output error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    # Step 3: Summarize the results.
    return summarize_workflow(
        result=result,
        output_paths=request.output_paths,
    )
