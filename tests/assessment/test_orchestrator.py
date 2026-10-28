"""Tests for the assessment orchestrator."""

import pytest

from pqc_inventory.assessment.interfaces import (
    AssessmentPolicy,
    AssessmentPolicyError,
)
from pqc_inventory.assessment.orchestrator import AssessmentOrchestrator
from pqc_inventory.assessment.registry import AssessmentPolicyRegistry


class StubPolicy(AssessmentPolicy):
    """Minimal policy implementation for orchestrator tests."""

    def __init__(self, policy_id: str) -> None:
        self._policy_id = policy_id

    @property
    def policy_id(self) -> str:
        return self._policy_id

    @property
    def policy_version(self) -> str:
        return "1.0.0"

    @property
    def policy_name(self) -> str:
        return f"Test Policy {self.policy_id}"

    @property
    def policy_description(self) -> str:
        return "A policy used for testing orchestration."

    def assess(self, context: dict) -> dict:
        """Return a minimal successful assessment result."""
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "execution_status": "completed",
            "findings": [],
            "limitations": [],
        }


class FailingPolicy(StubPolicy):
    """Policy that raises the expected assessment exception."""

    def assess(self, context: dict) -> dict:
        """Simulate a policy execution failure."""
        raise AssessmentPolicyError("Simulated policy failure.")


@pytest.fixture
def assessment_context():
    """Provide minimal context for an assessment run."""
    return {
        "domain": "example.com",
        "methodology_version": "1.0",
        "tls": {
            "target": "example.com",
            "scan_status": "completed",
        },
    }


@pytest.fixture
def registry():
    """Return an empty policy registry."""
    return AssessmentPolicyRegistry()


def test_run_assess_returns_assessment_metadata(
    registry,
    assessment_context,
):
    """The orchestrator should preserve the assessment metadata."""
    registry.register(StubPolicy("TEST-1"))
    orchestrator = AssessmentOrchestrator(registry)

    result = orchestrator.run_assess(
        context=assessment_context,
        assessment_run_id="run-123",
        created_at="2026-10-26T12:00:00Z",
    )

    assert result["schema_version"] == "1.0"
    assert result["assessment_run_id"] == "run-123"
    assert result["domain"] == "example.com"
    assert result["created_at"] == "2026-10-26T12:00:00Z"
    assert result["methodology_version"] == "1.0"
    assert result["evidence"] == assessment_context["tls"]


def test_run_assess_collects_policy_results(
    registry,
    assessment_context,
):
    """The orchestrator should collect results from registered policies."""
    registry.register(StubPolicy("TEST-1"))
    registry.register(StubPolicy("TEST-2"))
    orchestrator = AssessmentOrchestrator(registry)

    result = orchestrator.run_assess(
        context=assessment_context,
        assessment_run_id="run-123",
        created_at="2026-10-26T12:00:00Z",
    )

    assert set(result["assessments"]) == {"TEST-1", "TEST-2"}
    assert result["assessments"]["TEST-1"]["execution_status"] == "completed"
    assert result["assessments"]["TEST-2"]["execution_status"] == "completed"


def test_policy_error_is_recorded_without_stopping_other_policies(
    registry,
    assessment_context,
):
    """A policy error should be recorded while other policies still execute."""
    registry.register(FailingPolicy("FAIL-1"))
    registry.register(StubPolicy("TEST-2"))
    orchestrator = AssessmentOrchestrator(registry)

    result = orchestrator.run_assess(
        context=assessment_context,
        assessment_run_id="run-123",
        created_at="2026-10-26T12:00:00Z",
    )

    failed_result = result["assessments"]["FAIL-1"]
    successful_result = result["assessments"]["TEST-2"]

    assert failed_result["execution_status"] == "failed"
    assert failed_result["findings"] == []
    assert any(
        "Simulated policy failure." in limitation
        for limitation in failed_result["limitations"]
    )
    assert successful_result["execution_status"] == "completed"


def test_run_assess_with_empty_registry_returns_no_assessments(
    registry,
    assessment_context,
):
    """An empty registry should produce a run with no policy results."""
    orchestrator = AssessmentOrchestrator(registry)

    result = orchestrator.run_assess(
        context=assessment_context,
        assessment_run_id="run-123",
        created_at="2026-10-26T12:00:00Z",
    )

    assert result["assessments"] == {}
