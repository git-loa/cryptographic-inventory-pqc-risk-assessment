"""Shared fixtures for reporting tests."""

import pytest

from pqc_inventory.application.report_data import ReportData


@pytest.fixture
def report_data() -> ReportData:
    """Create representative structured data for report-rendering tests."""

    finding = {
        "finding_id": "finding-001",
        "policy_id": "A1",
        "dimension": "tls_version",
        "observed_value": "TLSv1.3",
        "classification": "acceptable",
        "rule_id": "A1-R1",
        "rationale": "TLS 1.3 was negotiated successfully.",
        "evidence_references": ["tls_version"],
    }

    def assessment_run(
        run_id: str,
        domain: str,
        scan_id: str,
        scan_status: str,
    ) -> dict:
        """Create an assessment run for a reporting test."""

        return {
            "schema_version": "1.0",
            "assessment_run_id": run_id,
            "domain": domain,
            "created_at": "2026-11-01T10:00:00Z",
            "methodology_version": "1.0",
            "evidence": {
                "schema_version": "1.0",
                "scan_id": scan_id,
                "target": domain,
                "target_type": "domain",
                "port": 443,
                "resolved_ip_address": "192.0.2.10",
                "scan_status": scan_status,
                "started_at": "2026-11-01T10:00:00Z",
                "completed_at": "2026-11-01T10:00:05Z",
                "scan_time_seconds": 5.0,
                "certificate_verification_status": "verified",
                "certificate_verification_error": None,
                "key_establishment_evidence_status": "observed",
                "extended_key_usage": None,
                "diagnostics": [],
            },
            "assessments": {
                "A1": {
                    "policy_id": "A1",
                    "policy_version": "1.0.0",
                    "execution_status": "completed",
                    "findings": [finding],
                    "limitations": [],
                }
            },
        }

    return {
        "metadata": {
            "report_title": "TLS Cryptographic Assessment Report",
            "report_id": "test-report-001",
            "generated_at": "2026-11-01T12:00:00Z",
            "author": "Test Author",
            "organization": "Test Organization",
            "report_version": "1.0",
        },
        "overview": {
            "total_assessment_runs": 2,
            "methodology_versions": ["1.0"],
            "policies_executed": ["A1"],
            "policy_execution_counts": {
                "completed": 2,
                "partial": 0,
                "failed": 0,
                "not_assessed": 0,
            },
            "scan_status_counts": {
                "completed": 1,
                "partial": 1,
                "failed": 0,
            },
            "classification_counts": {
                "acceptable": 2,
                "acceptable_with_review": 0,
                "unacceptable": 0,
                "unknown": 0,
            },
        },
        "assessment_runs": [
            assessment_run(
                run_id="run-001",
                domain="example.com",
                scan_id="scan-001",
                scan_status="completed",
            ),
            assessment_run(
                run_id="run-002",
                domain="example.org",
                scan_id="scan-002",
                scan_status="partial",
            ),
        ],
    }
