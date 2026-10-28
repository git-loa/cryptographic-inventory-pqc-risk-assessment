"""Tests for the TLS evidence assessment application service."""

import json
from unittest.mock import Mock
from uuid import UUID

import pytest

from pqc_inventory.application.assessment_service import AssessmentService
from pqc_inventory.assessment.policy_setup import create_default_registry


@pytest.fixture
def valid_evidence():
    """Provide a minimal valid TLS evidence record."""
    return {
        "schema_version": "1.0",
        "scan_id": "scan-001",
        "target": "example.com",
        "target_type": "domain",
        "port": 443,
        "resolved_ip_address": "192.0.2.10",
        "scan_status": "completed",
        "started_at": "2026-01-01T12:00:00Z",
        "completed_at": "2026-01-01T12:00:01Z",
        "scan_time_seconds": 1.0,
        "certificate_verification_status": "not_performed",
        "certificate_verification_error": None,
        "key_establishment_evidence_status": "unavailable",
        "diagnostics": [],
    }


@pytest.fixture
def service():
    """Create a service using the default policy registry."""
    return AssessmentService(
        registry=create_default_registry(),
        methodology_version="1.0",
    )


def test_assess_evidence_returns_one_assessment_run(service, valid_evidence):
    runs = service.assess_evidence(valid_evidence)

    assert len(runs) == 1

    run = runs[0]
    assert run["schema_version"] == "1.0"
    assert run["domain"] == "example.com"
    assert run["methodology_version"] == "1.0"
    assert run["evidence"] == valid_evidence
    assert "A1" in run["assessments"]


def test_assess_evidence_generates_valid_unique_run_ids(
    service,
    valid_evidence,
):
    runs = service.assess_evidence(
        evidence=[
            valid_evidence,
            valid_evidence,
        ]
    )

    assert len(runs) == 2

    run_ids = [run["assessment_run_id"] for run in runs]

    for run_id in run_ids:
        UUID(run_id)

    assert len(set(run_ids)) == 2


def test_assess_evidence_preserves_input_order(service, valid_evidence):
    second_evidence = {
        **valid_evidence,
        "scan_id": "scan-002",
        "target": "example.org",
    }

    runs = service.assess_evidence([valid_evidence, second_evidence])

    assert [run["domain"] for run in runs] == [
        "example.com",
        "example.org",
    ]
    assert [run["evidence"]["scan_id"] for run in runs] == [
        "scan-001",
        "scan-002",
    ]


def test_assess_evidence_can_select_specific_policy(
    service,
    valid_evidence,
):
    runs = service.assess_evidence(
        valid_evidence,
        policy_ids=["A1"],
    )

    assert len(runs) == 1
    assert list(runs[0]["assessments"]) == ["A1"]


def test_assess_evidence_rejects_empty_policy_selection(
    service,
    valid_evidence,
):
    with pytest.raises(
        ValueError,
        match="At least one assessment policy must be selected",
    ):
        service.assess_evidence(valid_evidence, policy_ids=[])


def test_assess_evidence_rejects_unknown_policy(
    service,
    valid_evidence,
):
    with pytest.raises(KeyError):
        service.assess_evidence(
            valid_evidence,
            policy_ids=["UNKNOWN"],
        )


def test_assess_evidence_rejects_invalid_evidence(service):
    with pytest.raises(ValueError):
        service.assess_evidence({"target": "example.com"})


def test_assess_file_loads_assesses_and_saves_results(
    valid_evidence,
    tmp_path,
):
    input_path = tmp_path / "tls-evidence.json"
    output_path = tmp_path / "assessment-results.json"

    input_path.write_text(
        json.dumps([valid_evidence]),
        encoding="utf-8",
    )

    service = AssessmentService(
        methodology_version="1.0",
    )

    runs = service.assess_file(
        input_path=input_path,
        output_path=output_path,
    )

    assert len(runs) == 1
    assert output_path.exists()

    saved_results = json.loads(output_path.read_text(encoding="utf-8"))

    assert len(saved_results) == 1
    assert saved_results[0]["domain"] == "example.com"
    assert "A1" in saved_results[0]["assessments"]


def test_assess_file_does_not_save_when_assessment_fails(
    tmp_path,
):
    repository = Mock()
    repository.load_json.return_value = {"invalid": "evidence"}

    service = AssessmentService(repository=repository)

    output_path = tmp_path / "assessment-results.json"

    with pytest.raises(ValueError):
        service.assess_file(
            input_path=tmp_path / "input.json",
            output_path=output_path,
        )

    repository.save_json.assert_not_called()
