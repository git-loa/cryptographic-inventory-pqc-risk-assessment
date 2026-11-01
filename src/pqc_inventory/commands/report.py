"""CLI command for generating assessment reports."""

import argparse


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the report command and its arguments."""

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
