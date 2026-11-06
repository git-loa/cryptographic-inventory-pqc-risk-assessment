"""
Command-line interface for TLS cryptographic inventory and assessment.
"""

import argparse
from collections.abc import Callable, Sequence

from pqc_inventory.config.bootstrap import initialize_workspace
from pqc_inventory.commands.policies import (
    register_parser as register_policies_parser,
    run_policies,
)
from pqc_inventory.commands.scan import (
    register_parser as register_scan_parser,
    run_scan,
)
from pqc_inventory.commands.assess import (
    register_parser as register_assess_parser,
    run_assess,
)
from pqc_inventory.commands.report import (
    register_parser as register_report_parser,
    run_report,
)

from pqc_inventory.commands.run import (
    register_parser as register_run_parser,
)

from pqc_inventory.commands.constants import EXIT_ERROR, EXIT_SUCCESS

APP_NAME = "pqc-assessment"
APP_VERSION = "0.1.0"

CommandHandler = Callable[[argparse.Namespace], int]
COMMAND_HANDLERS: dict[str, CommandHandler] = {
    "policies": run_policies,
    "scan": run_scan,
    "assess": run_assess,
    "report": run_report,
}

WORKSPACE_COMMANDS: set[str] = {
    "scan",
    "assess",
    "report",
}


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

    register_policies_parser(subparsers)
    register_scan_parser(subparsers)
    register_assess_parser(subparsers)
    register_report_parser(subparsers)
    register_run_parser(subparsers)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse command-line arguments and dispatch the requested command."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return EXIT_SUCCESS

    handler = COMMAND_HANDLERS.get(args.command)

    if handler is None:
        parser.error(f"No handler registered for command '{args.command}'.")

    if args.command in WORKSPACE_COMMANDS:
        try:
            args.workspace = initialize_workspace()
        except (OSError, ValueError) as exc:
            parser.exit(
                EXIT_ERROR,
                f"Workspace initialization failed: {exc}\n",
            )

    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
