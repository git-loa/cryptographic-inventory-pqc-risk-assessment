"""
Pipeline Orchestrator for TLS + PQC Analysis.

Runs each stage as an isolated subprocess and ensures required resources
exist before execution. Supports individual stage execution or a unified
--all mode.
"""

import os
import time
import argparse
import subprocess
from pathlib import Path
import sys

from rich.console import Console
from rich.text import Text

from src.scanner.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)
PYTHON_EXECUTABLE = sys.executable


# -----------------------------
# Resource Checking
# -----------------------------


def check_file(path: str) -> bool:
    """Return True if the file exists."""
    return Path(path).exists()


def run_stage(
    name: str, cmd: list[str], required_files: list[str], debug: bool = False
) -> None:
    """
    Execute a pipeline stage via subprocess if all required files exist.
    """
    console.print(Text(f"\n=== Running stage: {name} ===", style="bold cyan"))
    logger.info("Starting stage: %s", name)

    for f in required_files:
        if not check_file(f):
            logger.warning("Skipping stage '%s'; missing resource: %s", name, f)
            console.print(
                Text(f"[SKIP] Missing required resource: {f}", style="yellow")
            )
            console.print(Text(f"[SKIP] Stage '{name}' will not run.", style="yellow"))
            return

    env = {**os.environ, "PIPELINE_DEBUG": "1" if debug else "0"}

    start_time = time.perf_counter()
    try:
        subprocess.run(cmd, check=True, env=env)
        elapsed_time = time.perf_counter() - start_time
        logger.info("Stage '%s' completed in %.2f seconds", name, elapsed_time)
        console.print(
            Text(
                f"[OK] Stage '{name}' complete in {elapsed_time:.2f} seconds.",
                style="green",
            )
        )
    except subprocess.CalledProcessError as exc:
        logger.error("Stage '%s' failed: %s", name, exc)
        console.print(Text(f"[ERROR] Stage '{name}' failed.", style="bold red"))


# -----------------------------
# CLI Pipeline
# -----------------------------


def main() -> None:
    """Parse CLI arguments and execute requested pipeline stages."""
    parser = argparse.ArgumentParser(description="TLS + PQC Pipeline Runner")

    # Core pipeline stages
    parser.add_argument("--runscanner", action="store_true", help="Run TLS scanner")
    parser.add_argument("--scorepqc", action="store_true", help="Run PQC scoring")
    parser.add_argument(
        "--combined", action="store_true", help="Generate combined TLS+PQC JSON"
    )
    parser.add_argument(
        "--markdown", action="store_true", help="Generate Markdown report"
    )
    parser.add_argument(
        "--author", default="Unknown Author", help="Name of the report author"
    )
    parser.add_argument(
        "--organization",
        default="Independent Researcher",
        help="Organization or affiliation",
    )

    parser.add_argument("--all", action="store_true", help="Run all stages in order")

    # Printing
    parser.add_argument(
        "--print-tls-results", action="store_true", help="Print saved TLS results"
    )
    parser.add_argument(
        "-s", "--summary", action="store_true", help="Print summary table"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print detailed results"
    )

    # New features
    parser.add_argument(
        "--domains", default="config/domains.txt", help="Path to domains file"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # -----------------------------
    # Logging level control
    # -----------------------------
    if args.debug:
        logger.setLevel("DEBUG")
        console.print(Text("[DEBUG] Debug logging enabled", style="magenta"))
        logger.debug("Debug mode activated")

    # -----------------------------
    # Unified Pipeline (--all)
    # -----------------------------
    if args.all:
        pipeline_start_time = time.perf_counter()

        logger.info("Executing full pipeline (--all)")

        run_stage(
            "TLS Scanner",
            [PYTHON_EXECUTABLE, "-m", "src.run_scan", "--domains", args.domains],
            [args.domains],
            debug=args.debug,
        )

        run_stage(
            "PQC Scoring",
            [PYTHON_EXECUTABLE, "-m", "src.scanner.score_pqc_from_json"],
            ["data/processed/tls_results.json"],
            debug=args.debug,
        )

        run_stage(
            "Combined Report",
            [PYTHON_EXECUTABLE, "-m", "src.scanner.combined_report"],
            ["data/processed/tls_results.json", "data/processed/pqc_scores.json"],
            debug=args.debug,
        )

        run_stage(
            "Markdown Report",
            [
                PYTHON_EXECUTABLE,
                "-m",
                "src.scanner.markdown_report",
                "--author",
                args.author,
                "--organization",
                args.organization,
            ],
            ["reports/combined_report.json"],
            debug=args.debug,
        )

        pipeline_elapsed_time = time.perf_counter() - pipeline_start_time
        logger.info("Full pipeline completed in %.2f seconds", pipeline_elapsed_time)
        return

    # -----------------------------
    # Individual Pipeline Stages
    # -----------------------------
    if args.runscanner:
        run_stage(
            "TLS Scanner",
            [PYTHON_EXECUTABLE, "-m", "src.run_scan", "--domains", args.domains],
            [args.domains],
            debug=args.debug,
        )

    if args.scorepqc:
        run_stage(
            "PQC Scoring",
            [PYTHON_EXECUTABLE, "-m", "src.scanner.score_pqc_from_json"],
            ["data/processed/tls_results.json"],
            debug=args.debug,
        )

    if args.combined:
        run_stage(
            "Combined Report",
            [PYTHON_EXECUTABLE, "-m", "src.scanner.combined_report"],
            ["data/processed/tls_results.json", "data/processed/pqc_scores.json"],
            debug=args.debug,
        )

    if args.markdown:
        run_stage(
            "Markdown Report",
            [PYTHON_EXECUTABLE, "-m", "src.scanner.markdown_report"],
            ["reports/combined_report.json"],
            debug=args.debug,
        )

    # -----------------------------
    # TLS Results Printing
    # -----------------------------

    # pylint: disable=import-outside-toplevel
    if args.print_tls_results:
        logger.info("Printing TLS results")

        # Optional imports — only needed when printing
        from src.scanner.json_io import (
            load_tls_results,
        )
        from src.scanner.print_tls_results import (
            print_results_table,
            print_results_verbose,
        )

        if not check_file("data/processed/tls_results.json"):
            logger.error("Cannot print TLS results; tls_results.json missing")
            console.print(Text("[ERROR] TLS results file not found", style="bold red"))
            return

        results = load_tls_results()

        # Default: summary if no flags provided
        if not args.summary and not args.verbose:
            args.summary = True

        if args.summary:
            console.print(Text("\n=== TLS SUMMARY TABLE ===\n", style="bold cyan"))
            print_results_table(results)

        if args.verbose:
            console.print(Text("\n=== TLS VERBOSE DETAILS ===\n", style="bold cyan"))
            print_results_verbose(results)


if __name__ == "__main__":
    main()
