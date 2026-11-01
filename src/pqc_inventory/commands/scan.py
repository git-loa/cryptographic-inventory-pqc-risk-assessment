"""CLI command for collecting TLS evidence."""

import argparse
import sys
from pathlib import Path

from pqc_inventory.application.scan_service import ScanService

from pqc_inventory.collection.models import TLSScanResult
from pqc_inventory.collection.target_loader import load_targets
from pqc_inventory.collection.tls_utils import validate_target

from pqc_inventory.commands.common import resolve_output_path
from pqc_inventory.commands.common import valid_port
from pqc_inventory.commands.constants import (
    EXIT_SUCCESS,
    EXIT_ERROR,
    EXIT_INVALID_INPUT,
    EXIT_PARTIAL,
    EXIT_CANCELLED,
)
from pqc_inventory.storage.json_repository import (
    JSONRepository,
    JSONRepositoryError,
)


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


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the scan command and its arguments."""

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
