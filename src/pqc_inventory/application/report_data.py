"""Data contracts and aggregation logic for assessment reporting."""

from collections import Counter
from typing import TypedDict

from pqc_inventory.assessment.models import (
    AssessmentRun,
    AssessmentClassification,
    PolicyExecutionStatus,
)
from pqc_inventory.collection.models import ScanStatus


class ReportMetadata(TypedDict):
    """Metadata identifying a generated assessment report."""

    report_title: str
    report_id: str
    generated_at: str
    author: str
    organization: str
    report_version: str


class ClassificationCounts(TypedDict):
    """Counts of assessment findings grouped by classification."""

    acceptable: int
    acceptable_with_review: int
    unacceptable: int
    unknown: int


class PolicyExecutionCounts(TypedDict):
    """Counts of policy executions grouped by execution status."""

    completed: int
    partial: int
    failed: int
    not_assessed: int


class ScanStatusCounts(TypedDict):
    """Counts of TLS collection results grouped by scan status."""

    completed: int
    partial: int
    failed: int


class AssessmentOverview(TypedDict):
    """Aggregated statistics describing a collection of assessment runs."""

    total_assessment_runs: int
    methodology_versions: list[str]
    policies_executed: list[str]
    policy_execution_counts: PolicyExecutionCounts
    scan_status_counts: ScanStatusCounts
    classification_counts: ClassificationCounts


class ReportData(TypedDict):
    """Complete data context supplied to the assessment report renderer."""

    metadata: ReportMetadata
    overview: AssessmentOverview
    assessment_runs: list[AssessmentRun]


class ReportDataBuilder:
    """Build report-ready data from saved assessment runs."""

    def __init__(
        self,
        assessment_runs: list[AssessmentRun],
    ) -> None:
        """Initialize the builder with assessment runs."""
        self.assessment_runs = assessment_runs

    def build_overview(self) -> AssessmentOverview:
        """Aggregate summary statistics across assessment runs."""

        total_assessment_runs = len(self.assessment_runs)

        # Collect unique methodology versions.
        methodology_versions = sorted(
            {run["methodology_version"] for run in self.assessment_runs}
        )

        # Collect unique policy identifiers.
        policies_executed = sorted(
            {
                policy_id
                for run in self.assessment_runs
                for policy_id in run["assessments"]
            }
        )

        # Count policy execution outcomes.
        policy_counter = Counter[PolicyExecutionStatus](
            policy_record["result"]["execution_status"]
            for run in self.assessment_runs
            for policy_record in run["assessments"].values()
        )

        policy_execution_counts: PolicyExecutionCounts = {
            "completed": policy_counter["completed"],
            "partial": policy_counter["partial"],
            "failed": policy_counter["failed"],
            "not_assessed": policy_counter["not_assessed"],
        }

        # Count TLS collection outcomes.
        scan_counter = Counter[ScanStatus](
            run["evidence"]["scan_status"] for run in self.assessment_runs
        )

        scan_status_counts: ScanStatusCounts = {
            "completed": scan_counter["completed"],
            "partial": scan_counter["partial"],
            "failed": scan_counter["failed"],
        }

        # Count individual assessment findings.
        classification_counter = Counter[AssessmentClassification](
            finding["classification"]
            for run in self.assessment_runs
            for policy_record in run["assessments"].values()
            for finding in policy_record["result"]["findings"]
        )

        classification_counts: ClassificationCounts = {
            "acceptable": classification_counter["acceptable"],
            "acceptable_with_review": classification_counter["acceptable_with_review"],
            "unacceptable": classification_counter["unacceptable"],
            "unknown": classification_counter["unknown"],
        }

        return {
            "total_assessment_runs": total_assessment_runs,
            "methodology_versions": methodology_versions,
            "policies_executed": policies_executed,
            "policy_execution_counts": policy_execution_counts,
            "scan_status_counts": scan_status_counts,
            "classification_counts": classification_counts,
        }

    def build_report_data(
        self,
        metadata: ReportMetadata,
    ) -> ReportData:
        """Build the complete report data structure."""

        return {
            "metadata": metadata,
            "overview": self.build_overview(),
            "assessment_runs": self.assessment_runs,
        }
