"""Tests for the assessment orchestrator."""

import pytest

from pqc_inventory.assessment.interfaces import (
    AssessmentPolicy,
    AssessmentPolicyError,
)
from pqc_inventory.assessment.orchestrator import AssessmentOrchestrator
from pqc_inventory.assessment.registry import AssessmentPolicyRegistry
from pqc_inventory.assessment.models import (
    PolicyMetadata,
    PolicyRule,
)


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

    @property
    def metadata(self) -> PolicyMetadata:
        """Return metadata describing the test policy."""

        return PolicyMetadata(
            policy_id=self.policy_id,
            name=self.policy_name,
            version=self.policy_version,
            description=self.policy_description,
            scope=("Test assessment scope",),
            rules=(
                PolicyRule(
                    rule_id=f"{self.policy_id}.1",
                    name="Test Rule",
                    description="A rule used for testing.",
                    dimension="test_dimension",
                    evaluation_summary="Classifies test evidence.",
                ),
            ),
        )


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
    """The orchestrator should collect policy metadata and execution results."""

    registry.register(StubPolicy("TEST-1"))
    registry.register(StubPolicy("TEST-2"))
    orchestrator = AssessmentOrchestrator(registry)

    result = orchestrator.run_assess(
        context=assessment_context,
        assessment_run_id="run-123",
        created_at="2026-10-26T12:00:00Z",
    )

    assert set(result["assessments"]) == {"TEST-1", "TEST-2"}

    first_policy = result["assessments"]["TEST-1"]

    assert first_policy["metadata"]["policy_id"] == "TEST-1"
    assert first_policy["metadata"]["name"] == "Test Policy TEST-1"
    assert first_policy["metadata"]["rules"][0]["rule_id"] == "TEST-1.1"

    assert first_policy["result"]["execution_status"] == "completed"
    assert first_policy["result"]["policy_id"] == "TEST-1"

    assert result["assessments"]["TEST-2"]["result"]["execution_status"] == (
        "completed"
    )


def test_policy_error_is_recorded_without_stopping_other_policies(
    registry,
    assessment_context,
):
    """A policy error should be recorded without stopping other policies."""

    registry.register(FailingPolicy("FAIL-1"))
    registry.register(StubPolicy("TEST-2"))
    orchestrator = AssessmentOrchestrator(registry)

    result = orchestrator.run_assess(
        context=assessment_context,
        assessment_run_id="run-123",
        created_at="2026-10-26T12:00:00Z",
    )

    failed_record = result["assessments"]["FAIL-1"]
    successful_record = result["assessments"]["TEST-2"]

    # Metadata must be preserved even when execution fails.
    assert failed_record["metadata"]["policy_id"] == "FAIL-1"
    assert failed_record["metadata"]["name"] == "Test Policy FAIL-1"

    # Failed execution result.
    assert failed_record["result"]["execution_status"] == "failed"
    assert failed_record["result"]["findings"] == []

    assert any(
        "Simulated policy failure." in limitation
        for limitation in failed_record["result"]["limitations"]
    )

    # Other policies must continue executing.
    assert successful_record["result"]["execution_status"] == "completed"


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
