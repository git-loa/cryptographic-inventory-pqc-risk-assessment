"""
Combined TLS + PQC Report Generator

This module loads TLS scan results and PQC scoring results from JSON,
merges them into CombinedTLSReport objects, and writes a final combined
report to reports/combined_report.json.

This is the final stage of the TLS → PQC → Reporting pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.scanner.json_io import load_tls_results, load_pqc_scores
from src.scanner.models import CombinedTLSReport
from src.scanner.utils.report_utils import build_combined_reports


def save_combined_reports(
    reports: list[CombinedTLSReport],
    path: str | Path = "reports/combined_report.json",
) -> None:
    """
    Save combined TLS + PQC reports to JSON.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2)


def main() -> None:
    """
    Load TLS + PQC JSON, merge them, and save the combined report.
    """
    tls_results = load_tls_results()
    pqc_scores = load_pqc_scores()

    combined_reports = build_combined_reports(tls_results, pqc_scores)
    save_combined_reports(combined_reports)

    print("Combined TLS + PQC report generated.")
    print("Saved to reports/combined_report.json")


if __name__ == "__main__":
    main()
