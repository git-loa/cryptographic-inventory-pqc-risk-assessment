"""Generate a sample TLS assessment and Markdown report."""

from pathlib import Path

from pqc_inventory.application.assessment_service import AssessmentService
from pqc_inventory.application.report_request import ReportRequest
from pqc_inventory.application.report_service import ReportService

PROJECT_ROOT = Path(__file__).resolve().parent

EVIDENCE_PATH = PROJECT_ROOT / "examples" / "sample_tls_evidence.json"

ASSESSMENT_PATH = PROJECT_ROOT / "artifacts" / "sample_assessment_run.json"

REPORT_PATH = PROJECT_ROOT / "artifacts" / "sample_assessment_report.md"


def main() -> None:
    """Generate and save an assessment run and its Markdown report."""

    # Step 1: Validate TLS evidence and execute the registered policies.
    assessment_service = AssessmentService(
        methodology_version="1.0",
    )

    assessment_runs = assessment_service.assess_file(
        input_path=EVIDENCE_PATH,
        output_path=ASSESSMENT_PATH,
    )

    print(f"Assessment runs generated: {len(assessment_runs)}")
    print(f"Assessment JSON: {ASSESSMENT_PATH}")

    # Step 2: Generate the Markdown report from saved assessment data.
    report_service = ReportService()

    request = ReportRequest(
        input_path=ASSESSMENT_PATH,
        output_path=REPORT_PATH,
        author="PQC Assessment Framework",
        organization="Sample Assessment",
        report_format="markdown",
    )

    generated_report = report_service.generate_report(request)

    print(f"Markdown report generated: {generated_report}")


if __name__ == "__main__":
    main()
