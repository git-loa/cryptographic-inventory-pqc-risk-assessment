"""CLI command for assessing collected TLS evidence."""

import argparse


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the assessment command and its arguments."""

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
        help="Policy to execute; may be specified more than once.",
    )
