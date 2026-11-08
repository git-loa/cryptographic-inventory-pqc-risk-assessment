"""Tests for HTML assessment report rendering."""

from pqc_inventory.reporting.html_renderer import HTMLReportRenderer


def test_renderer_escapes_dynamic_metadata(report_data):
    """Verify that dynamic metadata is safely escaped in HTML output."""

    report_data["metadata"]["author"] = "<script>alert('xss')</script>"

    renderer = HTMLReportRenderer()

    html = renderer.render(report_data=report_data)

    assert "&lt;script&gt;" in html
    assert "&lt;/script&gt;" in html
    assert "<script>alert('xss')</script>" not in html
