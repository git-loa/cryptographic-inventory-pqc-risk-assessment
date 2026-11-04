"""Service for generating assessment reports in multiple formats."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from uuid import uuid4

from pqc_inventory.application.assessment_run_validator import (
    AssessmentRunValidator,
)
from pqc_inventory.application.report_data import (
    ReportData,
    ReportDataBuilder,
    ReportMetadata,
)
from pqc_inventory.application.report_request import (
    ReportRequest,
    BatchReportRequest,
)
from pqc_inventory.collection.tls_utils import utc_now
from pqc_inventory.reporting.interfaces import ReportRenderer
from pqc_inventory.reporting.markdown_renderer import MarkdownReportRenderer
from pqc_inventory.storage.json_repository import JSONRepository

REPORT_TITLE = "TLS Cryptographic Assessment Report"
REPORT_VERSION = "1.0"

REPORT_FILENAMES = {
    "markdown": "assessment_report.md",
    "html": "assessment_report.html",
    "pdf": "assessment_report.pdf",
}


class ReportService:  # pylint: disable=too-few-public-methods
    """Coordinate the generation and persistence of assessment reports."""

    def __init__(
        self,
        repository: JSONRepository | None = None,
        renderers: Mapping[str, ReportRenderer] | None = None,
    ) -> None:
        """Initialize the report service and its dependencies.

        Args:
            repository: Repository used to load assessment data.
                Defaults to a new JSONRepository instance.
            renderers: Mapping of report formats to their renderers.
                Defaults to a MarkdownReportRenderer.
        """
        self.repository = repository if repository is not None else JSONRepository()

        self.renderers = (
            dict(renderers)
            if renderers is not None
            else {"markdown": MarkdownReportRenderer()}
        )

    def generate_report(self, request: ReportRequest) -> Path:
        """Generate and save a report in the requested format.

        Loads and validates assessment data, builds structured report
        data, renders the requested format, and persists the result.

        Args:
            request: Configuration specifying the input, output,
                author, organization, and requested report format.

        Returns:
            Path to the generated report.

        Raises:
            ValueError: If the requested format is unsupported or
                the assessment data fails validation.
            OSError: If the report cannot be written to disk.
        """
        report_data = self._build_report_data(
            input_path=request.input_path,
            author=request.author,
            organization=request.organization,
        )

        renderer = self._get_renderer(request.report_format)

        rendered_content = renderer.render(report_data=report_data)

        return self._save_report(
            content=rendered_content,
            output_path=request.output_path,
        )

    def generate_all_reports(
        self,
        request: BatchReportRequest,
    ) -> list[Path]:
        """Generate reports in every registered format.

        Loads and validates assessment data once, then passes the
        same structured report data to every registered renderer.

        Args:
            request: Configuration specifying the input, output directory,
                author, and organization.

        Returns:
            Paths to all generated reports.

        Raises:
            ValueError: If assessment data fails validation or a
                registered format has no configured output filename.
            OSError: If a report cannot be written to disk.
        """
        report_data = self._build_report_data(
            input_path=request.input_path,
            author=request.author,
            organization=request.organization,
        )

        destination_directory = request.output_directory
        destination_directory.mkdir(parents=True, exist_ok=True)

        generated_reports = []

        for report_format, renderer in self.renderers.items():
            filename = REPORT_FILENAMES.get(report_format)

            if filename is None:
                raise ValueError(
                    f"No output filename configured for format: {report_format}"
                )

            rendered_content = renderer.render(report_data=report_data)

            destination = destination_directory / filename

            saved_path = self._save_report(
                content=rendered_content,
                output_path=destination,
            )

            generated_reports.append(saved_path)

        return generated_reports

    def _build_report_data(
        self,
        input_path: str | Path,
        author: str,
        organization: str,
    ) -> ReportData:
        """Load, validate, and prepare structured report data.

        Args:
            input_path: Path to the assessment JSON file.
            author: Name of the report author.
            organization: Organization associated with the report.

        Returns:
            Structured report data shared by all renderers.
        """
        raw_assessment_runs = self.repository.load_json(input_path)

        assessment_runs = AssessmentRunValidator.validate(raw_assessment_runs)

        report_data_builder = ReportDataBuilder(assessment_runs)

        report_metadata = self._build_report_metadata(
            author=author,
            organization=organization,
        )

        return report_data_builder.build_report_data(report_metadata)

    def _get_renderer(self, report_format: str) -> ReportRenderer:
        """Retrieve the renderer registered for a report format.

        Args:
            report_format: Requested report format.

        Returns:
            The renderer registered for that format.

        Raises:
            ValueError: If no renderer is registered for the format.
        """
        renderer = self.renderers.get(report_format)

        if renderer is None:
            raise ValueError(
                f"Unsupported report format: {report_format}. "
                f"Available formats: {', '.join(self.renderers)}"
            )

        return renderer

    @staticmethod
    def _save_report(
        content: str | bytes,
        output_path: str | Path,
    ) -> Path:
        """Persist rendered report content to the filesystem.

        Text content is written using UTF-8 encoding.
        Binary content is written without text encoding.

        Args:
            content: Rendered report content.
            output_path: Destination path for the report.

        Returns:
            Path to the saved report.
        """
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            destination.write_bytes(content)
        else:
            destination.write_text(content, encoding="utf-8")

        return destination

    def _build_report_metadata(
        self,
        author: str,
        organization: str,
    ) -> ReportMetadata:
        """Create identifying metadata for an assessment report.

        Generates a unique report identifier and UTC timestamp.

        Args:
            author: Name of the report author.
            organization: Organization associated with the report.

        Returns:
            ReportMetadata containing the report title, identifier,
            generation timestamp, author, organization, and version.
        """
        return {
            "report_title": REPORT_TITLE,
            "report_id": str(uuid4()),
            "generated_at": utc_now(),
            "author": author,
            "organization": organization,
            "report_version": REPORT_VERSION,
        }
