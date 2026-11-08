"""Application service for orchestrating the complete assessment workflow."""

from dataclasses import dataclass
from pathlib import Path

from pqc_inventory.application.scan_service import ScanService
from pqc_inventory.application.assessment_service import AssessmentService
from pqc_inventory.application.report_service import ReportService
from pqc_inventory.application.report_request import ReportRequest
from pqc_inventory.application.workflow_request import WorkflowRequest
from pqc_inventory.assessment.models import AssessmentRun
from pqc_inventory.collection.models import TLSScanResult
from pqc_inventory.storage.json_repository import JSONRepository


@dataclass(frozen=True)
class WorkflowResult:
    """Represent the results produced by a complete workflow execution."""

    scan_results: tuple[TLSScanResult, ...]
    assessment_runs: tuple[AssessmentRun, ...]
    report_path: Path


class WorkflowService:  # pylint: disable=too-few-public-methods
    """Coordinate TLS collection, assessment, and report generation."""

    def __init__(
        self,
        scan_service: ScanService | None = None,
        assessment_service: AssessmentService | None = None,
        report_service: ReportService | None = None,
        repository: JSONRepository | None = None,
    ) -> None:
        """Initialize workflow dependencies."""

        self._repository = repository if repository is not None else JSONRepository()

        self._scan_service = scan_service if scan_service is not None else ScanService()

        self._assessment_service = (
            assessment_service
            if assessment_service is not None
            else AssessmentService(repository=self._repository)
        )

        self._report_service = (
            report_service
            if report_service is not None
            else ReportService(repository=self._repository)
        )

    def execute(self, request: WorkflowRequest) -> WorkflowResult:
        """Execute the complete TLS assessment and reporting workflow.

        Args:
            request: Configuration containing targets, policies,
                output destinations, and report metadata.

        Returns:
            WorkflowResult containing scan evidence, assessment runs,
            and the generated report path.

        Raises:
            ValueError: If workflow inputs or evidence are invalid.
            KeyError: If a requested assessment policy is unavailable.
            OSError: If filesystem operations fail.
        """

        # Step 1: Collect TLS evidence.
        scan_results = self._scan_service.scan_many(
            targets=request.targets,
            port=request.port,
        )

        # Step 2: Persist collected evidence.
        self._repository.save_json(
            path=request.output_paths.evidence,
            data=scan_results,
        )

        # Step 3: Assess collected TLS evidence.
        assessment_runs = self._assessment_service.assess_file(
            input_path=request.output_paths.evidence,
            output_path=request.output_paths.assessment,
            policy_ids=request.policy_ids,
        )

        # Step 4: Generate the assessment report.
        report_request = ReportRequest(
            input_path=request.output_paths.assessment,
            output_path=request.output_paths.report,
            author=request.author,
            organization=request.organization,
            report_format="markdown",
        )

        report_path = self._report_service.generate_report(
            request=report_request,
        )

        # Step 5: Return the workflow results.
        return WorkflowResult(
            scan_results=tuple(scan_results),
            assessment_runs=tuple(assessment_runs),
            report_path=report_path,
        )
