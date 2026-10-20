"""
Combined TLS and A1 assessment report generator.

Loads saved TLS scan results, runs the A1 assessment, and writes
the combined evidence and findings to a JSON report.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.scanner.assessment import assess_tls_results
from src.scanner.json_io import load_tls_results
from src.scanner.models import CombinedTLSReport


def save_combined_reports(
    reports: list[CombinedTLSReport],
    path: str | Path = "reports/combined_report.json",
) -> None:
    """Save combined TLS and A1 assessment reports to JSON."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(reports, file, indent=2)

    print(f"Combined assessment report saved to {output_path}")


def main() -> None:
    """Generate an A1 assessment report from saved TLS scan results."""
    tls_results = load_tls_results()
    combined_reports = assess_tls_results(tls_results)

    save_combined_reports(combined_reports)


if __name__ == "__main__":
    main()
