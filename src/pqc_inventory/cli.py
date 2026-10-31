"""
Command-line interface for TLS cryptographic inventory and assessment.
"""

from pathlib import Path
import sys
import argparse


from collections.abc import Sequence

from pqc_inventory.collection.models import TLSScanResult
from pqc_inventory.assessment.policy_setup import create_default_registry
from pqc_inventory.application.scan_service import ScanService
from pqc_inventory.collection.target_loader import load_targets
from pqc_inventory.collection.tls_utils import validate_target
from pqc_inventory.storage.json_repository import (
    JSONRepository,
    JSONRepositoryError,
)

APP_NAME = "pqc-assessment"
APP_VERSION = "0.1.0"

# Application exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_INVALID_INPUT = 2
EXIT_PARTIAL = 3
EXIT_CANCELLED = 4


def valid_port(value: str) -> int:
    """Validate and return a TCP port number."""
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Port must be an integer.") from exc

    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("Port must be between 1 and 65535.")

    return port


def build_parser() -> argparse.ArgumentParser:
    """Build and return the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description=(
            "Collect TLS cryptographic evidence, assess selected "
            "configuration properties, and generate reports."
        ),
        epilog=("Use '<command> --help' for command-specific options."),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {APP_VERSION}",
        help="Display the application version and exit.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available operations",
        metavar="<command>",
    )

    # Scan command
    scan_parser = subparsers.add_parser(
        "scan",
        help="Collect TLS evidence from endpoints.",
        description="Scan TLS endpoints and save collected evidence.",
    )

    scan_input = scan_parser.add_mutually_exclusive_group(required=True)
    scan_input.add_argument(
        "--targets",
        nargs="+",
        metavar="TARGET",
        help="One or more domain names or IP addresses to scan.",
    )
    scan_input.add_argument(
        "--targets-file",
        metavar="PATH",
        help="Path to a file containing domain names or IP addresses to scan.",
    )

    scan_parser.add_argument(
        "--port",
        type=valid_port,
        default=443,
        help="TLS endpoint port (default: 443).",
    )

    scan_parser.add_argument(
        "--output",
        default="data/evidence/tls_scans.json",
        help=(
            "Path where collected TLS evidence will be saved "
            "(default: data/evidence/tls_scans.json)"
        ),
    )

    # Assess commands
    assess_parser = subparsers.add_parser(
        "assess",
        help="Assess previously collected TLS evidence.",
        description="Evaluate saved TLS evidence using assessment policies.",
    )
    assess_parser.add_argument(
        "--input",
        required=True,
        help="Path to the saved TLS evidence JSON file.",
    )
    assess_parser.add_argument(
        "--output",
        default="data/assessments/assessment_runs.json",
        help=(
            "Path where assessment results will be saved "
            "(default: data/assessments/assessment_runs.json)."
        ),
    )
    assess_parser.add_argument(
        "--policy",
        action="append",
        dest="policies",
        metavar="POLICY_ID",
        help="Policy to execute; may be specified more than once",
    )

    # Report command
    report_parser = subparsers.add_parser(
        "report",
        help="Generate a report from assessment results.",
        description="Render saved assessment results into a report.",
    )
    report_parser.add_argument(
        "--input",
        required=True,
        help="Path to the saved assessment results JSON file.",
    )
    report_parser.add_argument(
        "--output",
        default="reports/assessment_report.md",
        help=(
            "Destination path for the generated Markdown report "
            "(default: reports/assessment_report.md)."
        ),
    )
    report_parser.add_argument(
        "--format",
        choices=["markdown"],
        default="markdown",
        help="Report format (default: markdown).",
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

    # Run command
    run_parser = subparsers.add_parser(
        "run",
        help="Run the complete scan, assessment, and reporting workflow.",
        description="Scan endpoints, assess evidence, and generate a report.",
    )
    run_input = run_parser.add_mutually_exclusive_group(required=True)
    run_input.add_argument(
        "--target",
        help="Single domain to scan.",
    )
    run_input.add_argument(
        "--targets",
        help="Path to a file containing domains to scan.",
    )
    run_parser.add_argument(
        "--port",
        type=valid_port,
        default=443,
        help="TLS endpoint port (default: 443).",
    )
    run_parser.add_argument(
        "--policy",
        action="append",
        dest="policies",
        metavar="POLICY_ID",
        help="Policy to execute; may be specified more than once.",
    )
    run_parser.add_argument(
        "--output",
        default="reports/assessment_report.md",
        help=(
            "Destination path for the generated Markdown report "
            "(default: reports/assessment_report.md)."
        ),
    )

    # Policies command
    subparsers.add_parser(
        "policies",
        help="List registered assessment policies.",
        description="Display the assessment policies available in the application.",
    )

    return parser


def list_policies() -> int:
    """Display the policies registered in the application."""
    registry = create_default_registry()
    policies = registry.all()

    if not policies:
        print("No assessment policies are registered.")
        return EXIT_SUCCESS

    print()
    print("Registered Assessment Policies")
    print("===============================")
    print()

    for policy in policies:
        print(f"ID:          {policy.policy_id}")
        print(f"Name:        {policy.policy_name}")
        print(f"Version:     {policy.policy_version}")
        print(f"Description: {policy.policy_description}")
        print()

    print(f"Total policies: {len(policies)}")
    print()
    return EXIT_SUCCESS


def validate_output_path(output_path: str | Path) -> Path:
    """Validate and normalize a JSON output path.

    Checks that the destination has a JSON file extension, that an
    existing destination is a regular file, and that an existing
    parent path is a directory.

    Args:
        output_path: The proposed destination for the JSON output file.

    Returns:
        The validated output path with the user's home directory expanded.

    Raises:
        ValueError: If the extension is invalid, the destination exists
            but is not a regular file, or the parent path is not a directory.
    """
    path = Path(output_path).expanduser()

    if path.suffix.lower() != ".json":
        raise ValueError("Output file must have a .json extension.")

    if path.exists() and not path.is_file():
        raise ValueError(f"Output path exists but is not a regular file: {path}")

    if path.parent.exists() and not path.parent.is_dir():
        raise ValueError(f"Output directory is not a directory: {path.parent}")

    return path


def resolve_output_path(output_path: str | Path) -> Path | None:
    """Resolve the evidence destination and prevent accidental overwrites.

    Validates the proposed destination and interacts with the user when
    the path is invalid or the output file already exists. The user may
    approve overwriting an existing file, choose another destination,
    or cancel the operation.

    Args:
        output_path: The proposed destination for the evidence JSON file.

    Returns:
        The approved output path, or None if the user cancels the operation.

    Raises:
        EOFError: If standard input closes while awaiting user input.
        KeyboardInterrupt: If the user interrupts the operation.
    """
    while True:
        try:
            path = validate_output_path(output_path)
        except ValueError as exc:
            print(f"Invalid output path: {exc}", file=sys.stderr)

            output_path = input(
                "Enter a valid JSON output path, or press Enter to cancel: "
            ).strip()

            if not output_path:
                print("Operation cancelled.")
                return None

            continue

        if not path.exists():
            return path

        print(f"\nOutput file already exists: {path}")
        print("1. Overwrite existing file")
        print("2. Choose another path")
        print("3. Cancel")

        choice = input("Choose an option [1-3]: ").strip()

        if choice == "1":
            confirmation = (
                input(f"Confirm overwrite of '{path}'? [y/N]: ").strip().lower()
            )

            if confirmation == "y":
                return path

            print("Overwrite not confirmed. No file was changed.")

        elif choice == "2":
            new_path = input("Enter the new output path: ").strip()

            if not new_path:
                print("Operation cancelled.")
                return None

            output_path = new_path

        elif choice == "3":
            print("Scan cancelled.")
            return None

        else:
            print("Invalid choice. Enter 1, 2, or 3.")


def collect_targets(args: argparse.Namespace) -> list[str]:
    """Load and validate TLS scan targets.

    Reads targets from the specified file or validates the targets
    supplied directly through command-line arguments. Valid targets
    are normalized before being returned.

    Args:
        args: Parsed command-line arguments containing either
            targets_file or targets.

    Returns:
        A list of validated and normalized target strings.

    Raises:
        ValueError: If any target is invalid.
        OSError: If the target file cannot be accessed or read.
    """
    if args.targets_file:
        return load_targets(args.targets_file)

    targets: list[str] = []

    for target in args.targets:
        _, normalized_target = validate_target(target)
        targets.append(normalized_target)

    return targets


def execute_scan(
    targets: list[str],
    port: int,
) -> list[TLSScanResult]:
    """Collect TLS evidence from the specified targets.

    Creates a scanning service and scans each target using the
    requested TCP port.

    Args:
        targets: Validated domain names or IP addresses to scan.
        port: TCP port used to establish TLS connections.

    Returns:
        The collected TLS scan results.

    Raises:
        Exception: If the scanning service encounters an unexpected
            error that prevents the scan operation from completing.
    """
    scanner = ScanService()

    return scanner.scan_many(
        targets=targets,
        port=port,
    )


def save_scan_results(
    results: list[TLSScanResult],
    output_path: Path,
) -> None:
    """Persist TLS scan results as JSON evidence.

    Delegates serialization and file handling to JSONRepository.

    Args:
        results: TLS scan results to persist.
        output_path: Approved destination for the evidence JSON file.

    Raises:
        JSONRepositoryError: If the repository cannot save the evidence.
        ValueError: If the output data or destination is invalid.
    """
    repository = JSONRepository()

    repository.save_json(
        path=output_path,
        data=results,
    )


def summarize_scan_results(
    results: list[TLSScanResult],
    output_path: Path,
) -> int:
    """Display scan statistics and determine the operation's exit code.

    Counts completed, partial, and failed scans, prints the evidence
    destination, and returns the appropriate exit code.

    Args:
        results: TLS scan results produced by the scanning service.
        output_path: Destination where the evidence was saved.

    Returns:
        EXIT_SUCCESS if all scans completed; otherwise, EXIT_PARTIAL.
    """
    completed = sum(result["scan_status"] == "completed" for result in results)
    partial = sum(result["scan_status"] == "partial" for result in results)
    failed = sum(result["scan_status"] == "failed" for result in results)

    print(f"Targets scanned: {len(results)}")
    print(f"Completed:       {completed}")
    print(f"Partial:         {partial}")
    print(f"Failed:          {failed}")
    print(f"Evidence saved:  {output_path}")

    if any(result["scan_status"] != "completed" for result in results):
        return EXIT_PARTIAL

    return EXIT_SUCCESS


def run_scan(args: argparse.Namespace) -> int:
    """Collect TLS evidence, save it, and report the scan outcome."""
    # Step 1: Validate targets.
    try:
        targets = collect_targets(args)
    except (ValueError, OSError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return EXIT_INVALID_INPUT

    # Step 2: Approve the output destination before network operations.
    try:
        output_path = resolve_output_path(args.output)
    except (EOFError, KeyboardInterrupt):
        print("\nScan cancelled.")
        return EXIT_CANCELLED

    if output_path is None:
        return EXIT_CANCELLED

    # Step 3: Collect TLS evidence.
    try:
        results = execute_scan(
            targets=targets,
            port=args.port,
        )
    except Exception as exc:
        print(f"Scanning error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    # Step 4: Persist the collected evidence.
    try:
        save_scan_results(
            results=results,
            output_path=output_path,
        )
    except (JSONRepositoryError, ValueError) as exc:
        print(f"Output error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    # Step 5: Report the outcome.
    return summarize_scan_results(
        results=results,
        output_path=output_path,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Parse command-line arguments and dispatch the requested command."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    # Listing policies
    if args.command == "policies":
        return list_policies()

    # Scan services
    if args.command == "scan":
        return run_scan(args)

    raise NotImplementedError(
        f"The '{args.command}' command has not been connected to its service yet."
    )


if __name__ == "__main__":
    raise SystemExit(main())
