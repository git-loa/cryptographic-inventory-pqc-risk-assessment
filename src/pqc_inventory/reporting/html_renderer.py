"""HTML rendering for cryptographic assessment reports."""

from jinja2 import (
    Environment,
    PackageLoader,
    StrictUndefined,
    Template,
)

from pqc_inventory.application.report_data import ReportData
from pqc_inventory.reporting.interfaces import ReportRenderer


class HTMLReportRenderer(ReportRenderer):  # pylint: disable=too-few-public-methods
    """Render assessment reports as standalone HTML documents."""

    def __init__(self) -> None:
        """Initialize the HTML rendering environment."""

        self.environment: Environment = Environment(
            loader=PackageLoader("pqc_inventory", "templates"),
            autoescape=True,
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self.template: Template = self.environment.get_template(
            "reports/assessment_report.html.j2"
        )

    def render(self, report_data: ReportData) -> str:
        """Render structured assessment data into HTML.

        Args:
            report_data: Structured assessment data.

        Returns:
            A complete HTML document.
        """

        return self.template.render(**report_data)
