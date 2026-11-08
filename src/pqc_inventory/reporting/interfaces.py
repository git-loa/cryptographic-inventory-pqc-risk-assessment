"""Define interfaces and contracts for assessment report rendering."""

from typing import Protocol

from pqc_inventory.application.report_data import ReportData


class ReportRenderer(Protocol):  # pylint: disable=too-few-public-methods
    """Define the contract for assessment report renderers."""

    def render(self, report_data: ReportData) -> str | bytes:
        """Render structured assessment data into a document.

        Args:
            report_data: Structured assessment data to render.

        Returns:
            The rendered document as text or binary content.
        """
        ...  # pylint: disable=unnecessary-ellipsis
