"""
Unit tests for the TLS + PQC Markdown report generator.
"""

from pathlib import Path
import tempfile

from src.scanner.markdown_report import (
    render_markdown,
    save_markdown,
)
from src.scanner.assessment import assess_tls_results


def test_assessment_combined_structure(tls_results):
    """Ensure assessment produces correctly structured combined reports."""
    _, combined = assess_tls_results(tls_results)

    assert isinstance(combined, list)
    assert len(combined) == len(tls_results)

    for report in combined:
        assert "domain" in report
        assert "tls" in report
        assert "a1" in report
        assert "pqc" in report
        assert report["domain"] == report["tls"]["domain"]
        assert report["domain"] == report["pqc"]["domain"]


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



def test_render_markdown_includes_a1_findings_for_failed_scan():
    """A1 evidence gaps remain visible even when the TLS scan fails."""
    _, reports = assess_tls_results(
        [{"domain": "unavailable.example", "port": 443, "error": "connect failed"}]
    )

    markdown = render_markdown(
        reports,
        author="Test",
        organization="Test Organization",
    )

    assert "A1 TLS Configuration Assessment" in markdown
    assert "TLS version" in markdown
    assert "cipher_suite" in markdown
    assert "unknown" in markdown
