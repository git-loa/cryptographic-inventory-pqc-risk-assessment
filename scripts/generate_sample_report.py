"""Generate a sample TLS assessment with Markdown and HTML reports."""

from pathlib import Path

from pqc_inventory.application.assessment_service import AssessmentService
from pqc_inventory.application.report_request import ReportRequest
from pqc_inventory.application.report_service import ReportService

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EVIDENCE_PATH = PROJECT_ROOT / "examples" / "sample_tls_evidence.json"

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

ASSESSMENT_PATH = ARTIFACTS_DIR / "sample_assessment_run.json"

REPORT_PATHS = {
    "markdown": ARTIFACTS_DIR / "sample_assessment_report.md",
    "html": ARTIFACTS_DIR / "sample_assessment_report.html",
}


def main() -> None:
    """Generate an assessment run and reports in supported formats."""

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

    # Step 2: Generate Markdown and HTML reports from saved assessment data.
    report_service = ReportService()

    for report_format, output_path in REPORT_PATHS.items():
        request = ReportRequest(
            input_path=ASSESSMENT_PATH,
            output_path=output_path,
            author="PQC Assessment Framework",
            organization="Sample Assessment",
            report_format=report_format,
        )

        generated_report = report_service.generate_report(request)

        print(f"{report_format.upper()} report generated: {generated_report}")


if __name__ == "__main__":
    main()
