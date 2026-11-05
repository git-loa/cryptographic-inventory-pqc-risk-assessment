"""Shared fixtures for application-layer tests."""

import pytest

from pqc_inventory.assessment.models import (
    AssessmentFinding,
    AssessmentRun,
    PolicyExecutionRecord,
    PolicyMetadataRecord,
    PolicyResult,
)
from pqc_inventory.collection.models import TLSScanResult


@pytest.fixture
def tls_scan_factory():
    """Create TLS scan evidence with configurable attributes."""

    def _create(
        scan_id: str = "scan-001",
        target: str = "example.com",
        scan_status: str = "completed",
    ) -> TLSScanResult:
        return {
            "schema_version": "1.0",
            "scan_id": scan_id,
            "target": target,
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
            "diagnostics": [],
        }

    return _create


@pytest.fixture
def policy_metadata_factory():
    """Create policy metadata records with configurable attributes."""

    def _create(
        policy_id: str = "A1",
        name: str | None = None,
        version: str = "1.0.0",
        description: str = "A test assessment policy.",
        scope: list[str] | None = None,
        rules: list[dict] | None = None,
        references: list[dict] | None = None,
    ) -> PolicyMetadataRecord:

        return {
            "policy_id": policy_id,
            "name": name if name is not None else f"Test Policy {policy_id}",
            "version": version,
            "description": description,
            "scope": (scope if scope is not None else ["Test assessment scope"]),
            "rules": (
                rules
                if rules is not None
                else [
                    {
                        "rule_id": f"{policy_id}.1",
                        "name": "Test Rule",
                        "description": "A rule used for testing.",
                        "dimension": "tls_version",
                        "evaluation_summary": ("Classifies the observed TLS version."),
                        "references": [],
                    }
                ]
            ),
            "references": references if references is not None else [],
        }

    return _create


@pytest.fixture
def policy_result_factory():
    """Create policy results with configurable findings and status."""

    def _create(
        policy_id: str = "A1",
        execution_status: str = "completed",
        findings: list[AssessmentFinding] | None = None,
    ) -> PolicyResult:
        return {
            "policy_id": policy_id,
            "policy_version": "1.0.0",
            "execution_status": execution_status,
            "findings": findings if findings is not None else [],
            "limitations": [],
        }

    return _create


@pytest.fixture
def policy_execution_record_factory(
    policy_metadata_factory,
    policy_result_factory,
):
    """Create policy execution records containing metadata and results."""

    def _create(
        policy_id: str = "A1",
        execution_status: str = "completed",
        findings: list[AssessmentFinding] | None = None,
        metadata: PolicyMetadataRecord | None = None,
    ) -> PolicyExecutionRecord:

        metadata_record = (
            metadata
            if metadata is not None
            else policy_metadata_factory(policy_id=policy_id)
        )

        result = policy_result_factory(
            policy_id=policy_id,
            execution_status=execution_status,
            findings=findings,
        )

        return {
            "metadata": metadata_record,
            "result": result,
        }

    return _create


@pytest.fixture
def assessment_run_factory(tls_scan_factory):
    """Create assessment runs with configurable evidence and assessments."""

    def _create(
        assessment_run_id: str = "run-001",
        domain: str = "example.com",
        methodology_version: str = "1.0",
        assessments: dict[str, PolicyExecutionRecord] | None = None,
        scan_status: str = "completed",
    ) -> AssessmentRun:
        return {
            "schema_version": "1.0",
            "assessment_run_id": assessment_run_id,
            "domain": domain,
            "created_at": "2026-11-01T10:00:00Z",
            "methodology_version": methodology_version,
            "evidence": tls_scan_factory(
                scan_id=f"scan-{assessment_run_id}",
                target=domain,
                scan_status=scan_status,
            ),
            "assessments": assessments if assessments is not None else {},
        }

    return _create


@pytest.fixture
def finding_factory():
    """Create assessment findings with configurable classifications."""

    def _create(
        finding_id: str = "finding-001",
        policy_id: str = "A1",
        classification: str = "acceptable",
        rule_id: str = "A1.1",
    ) -> AssessmentFinding:
        return {
            "finding_id": finding_id,
            "policy_id": policy_id,
            "dimension": "tls_version",
            "observed_value": "TLSv1.3",
            "classification": classification,
            "rule_id": rule_id,
            "rationale": "Test finding rationale.",
            "evidence_references": ["tls_version"],
        }

    return _create
