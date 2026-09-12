"""
Unit tests for the TLS + PQC Markdown report generator.
"""

from pathlib import Path
import tempfile

from src.scanner.markdown_report import (
    render_markdown,
    save_markdown,
)
from src.scanner.utils.report_utils import build_combined_reports


def test_build_combined_structure(tls_results, pqc_scores):
    """
    Ensure build_combined merges TLS + PQC entries correctly.
    """
    combined = build_combined_reports(tls_results, pqc_scores)

    assert isinstance(combined, list)
    assert len(combined) > 0

    first = combined[0]
    assert "domain" in first
    assert "tls" in first
    assert "pqc" in first


def test_render_markdown_basic(monkeypatch):
    """
    Ensure Markdown rendering works with a simple Jinja2 template.
    """

    # Minimal combined report
    reports = [
        {
            "domain": "example.com",
            "tls": {"domain": "example.com", "port": 443, "error": "DNS error"},
            "pqc": {
                "domain": "example.com",
                "tls_score": 0,
                "pqc_risk": "high",
                "reasons": ["x"],
            },
        }
    ]

    # Temporary template
    template_content = """
# TLS + PQC Report
Generated: {{ generated_at }}
Author: {{ author }}
Organization: {{ organization }}

{% for r in reports %}
## {{ r.domain }}
TLS Score: {{ r.pqc.tls_score }}
Risk: {{ r.pqc.pqc_risk }}
{% endfor %}
"""

    with tempfile.TemporaryDirectory() as tmp:
        template_path = Path(tmp) / "tls_pqc_report.md.j2"
        template_path.write_text(template_content, encoding="utf-8")

        # Monkeypatch load_template to use our temporary template
        def fake_load_template(_):
            return template_content

        monkeypatch.setattr(
            "src.scanner.markdown_report.load_template",
            fake_load_template,
        )

        md = render_markdown(
            reports,
            author="Leonard",
            organization="Quantum Sequrity",
        )

        # Basic checks
        assert "TLS + PQC Report" in md
        assert "Leonard" in md
        assert "Quantum Sequrity" in md
        assert "example.com" in md
        assert "high" in md


def test_save_markdown_writes_file():
    """
    Ensure save_markdown writes content to disk.
    """
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "report.md"
        content = "# Test Report\nHello world."

        save_markdown(content, path)

        assert path.exists()
        assert path.read_text(encoding="utf-8") == content
