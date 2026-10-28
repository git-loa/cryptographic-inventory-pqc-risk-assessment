"""
Command-line interface for TLS cryptographic inventory and assessment.
"""

import argparse

from collections.abc import Sequence

from pqc_inventory.assessment.policy_setup import create_default_registry

APP_NAME = "pqc-assessment"
APP_VERSION = "0.1.0"

# Application exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_INVALID_INPUT = 2
EXIT_PARTIAL = 3


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
        "--domain",
        help="Single domain to scan.",
    )
    scan_input.add_argument(
        "--domains",
        help="Path to a file containing domains to scan.",
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
            "Path where collected TLS evidence will be saved. "
            "default: data/evidence/tls_scans.json"
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
        "--domain",
        help="Single domain to scan.",
    )
    run_input.add_argument(
        "--domains",
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


def main(argv: Sequence[str] | None = None) -> int:
    """Parse command-line arguments and dispatch the requested command."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "policies":
        return list_policies()

    raise NotImplementedError(
        f"The '{args.command}' command has not been connected to its service yet."
    )


if __name__ == "__main__":
    raise SystemExit(main())
