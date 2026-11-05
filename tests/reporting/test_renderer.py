"""Tests for Markdown assessment report rendering."""

from pqc_inventory.reporting.markdown_renderer import MarkdownReportRenderer


def test_renderer_includes_report_metadata(report_data):
    """Verify that report metadata appears in the rendered Markdown."""

    renderer = MarkdownReportRenderer()

    markdown = renderer.render(report_data=report_data)

    assert "# TLS Cryptographic Assessment Report" in markdown
    assert "Test Organization" in markdown
    assert "Test Author" in markdown
    assert "test-report-001" in markdown


def test_renderer_generates_dynamic_table_of_contents(report_data):
    """Verify that every assessment target has a corresponding TOC entry."""

    renderer = MarkdownReportRenderer()

    markdown = renderer.render(report_data=report_data)

    assert "[Target 1: example.com](#target-1)" in markdown
    assert "[Target 2: example.org](#target-2)" in markdown

    assert '<a id="target-1"></a>' in markdown
    assert '<a id="target-2"></a>' in markdown


def test_renderer_wraps_each_target_in_collapsible_section(report_data):
    """Verify that assessment targets use collapsible Markdown sections."""

    renderer = MarkdownReportRenderer()

    markdown = renderer.render(report_data=report_data)

    assert markdown.count("<details>") == 2
    assert markdown.count("</details>") == 2

    assert (
        "<summary><strong>Target 1: example.com</strong>" " — 🟢 Completed</summary>"
    ) in markdown

    assert (
        "<summary><strong>Target 2: example.org</strong>" " — 🟠 Partial</summary>"
    ) in markdown


def test_renderer_includes_policy_findings(report_data):
    """Verify that policy findings and their classifications are rendered."""

    renderer = MarkdownReportRenderer()

    markdown = renderer.render(report_data=report_data)

    assert "finding-001" in markdown
    assert "A1-R1" in markdown
    assert "TLSv1.3" in markdown
    assert "TLS 1.3 was negotiated successfully." in markdown
    assert "🟢 Acceptable" in markdown


def test_renderer_handles_missing_extended_key_usage(report_data):
    """Verify that nullable extended key usage does not break rendering."""

    renderer = MarkdownReportRenderer()

    markdown = renderer.render(report_data=report_data)

    assert "No extended key usage information recorded." in markdown
