"""CLI command for executing the complete assessment workflow."""

import argparse

from pqc_inventory.commands.common import valid_port


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the complete workflow command and its arguments."""

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
