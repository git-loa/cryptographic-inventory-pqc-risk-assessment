"""
TLS + PQC Markdown Report Generator (Jinja2 Template Version)
"""

from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime

from jinja2 import Template

from src.scanner.json_io import load_tls_results, load_pqc_scores
from src.scanner.models import CombinedTLSReport
from src.scanner.utils.report_utils import (
    build_combined_reports,
    compute_top_findings,
)


def load_template(path: str | Path) -> str:
    """Load a Jinja2 template file."""
    return Path(path).read_text(encoding="utf-8")


def render_markdown(
    reports: list[CombinedTLSReport],
    author: str,
    organization: str,
) -> str:
    """Render Markdown using Jinja2 template."""
    template_text = load_template("templates/tls_pqc_report.md.j2")
    template = Template(template_text)

    # Compute top findings for summary section
    findings = compute_top_findings(reports)

    return template.render(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        author=author,
        organization=organization,
        reports=reports,
        findings=findings,
    )


def save_markdown(md: str, path: str | Path = "reports/tls_pqc_report.md") -> None:
    """Write Markdown content to file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(md, encoding="utf-8")


def main() -> None:
    """
    Load TLS + PQC JSON, merge, generate Markdown, save.

    NOTE:
    This module is invoked by the pipeline as a subprocess.
    The pipeline passes --author and --organization flags.
    """
    parser = argparse.ArgumentParser(description="Generate TLS + PQC Markdown Report")
    parser.add_argument("--author", default="Unknown Author")
    parser.add_argument("--organization", default="Independent Researcher")
    args = parser.parse_args()

    tls = load_tls_results()
    pqc = load_pqc_scores()
    combined = build_combined_reports(tls, pqc)

    md = render_markdown(
        combined,
        author=args.author,
        organization=args.organization,
    )
    save_markdown(md)

    print("[+] Markdown report generated.")
    print("[+] Saved to reports/tls_pqc_report.md")


if __name__ == "__main__":
    main()
