"""Markdown rendering for assessment reports."""

from jinja2 import Environment, PackageLoader, StrictUndefined, Template

from pqc_inventory.application.report_data import ReportData
from pqc_inventory.reporting.interfaces import ReportRenderer


class MarkdownReportRenderer(ReportRenderer):  # pylint: disable=too-few-public-methods
    """Render an assessment report as a Markdown document."""

    def __init__(self) -> None:
        """Initialize the Jinja2 rendering environment."""
        self.environment: Environment = Environment(
            loader=PackageLoader("pqc_inventory", "templates"),
            autoescape=False,
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.template: Template = self.environment.get_template(
            "reports/assessment_report.md.j2"
        )

    def render(self, report_data: ReportData) -> str:
        """Render assessment report data into Markdown.

        Args:
            report_data: Structured data containing report metadata,
                aggregated statistics, and assessment runs.

        Returns:
            The rendered Markdown document.
        """
        return self.template.render(**report_data)
