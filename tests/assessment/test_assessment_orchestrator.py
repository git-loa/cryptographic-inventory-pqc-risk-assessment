import pytest

from src.assessment.interfaces import AssessmentPolicyError
from src.assessment.models import AssessmentContext, PolicyResult
from src.assessment.orchestrator import AssessmentOrchestrator
from src.assessment.policies.a1_tls_configuration import (
    A1TLSConfigurationPolicy,
)
from src.assessment.registry import AssessmentPolicyRegistry


# pylint: disable = missing-function-docstring
class FailingPolicy:
    """Test policy that raises an expected assessment error."""

    @property
    def policy_id(self) -> str:
        return "TEST-FAIL"

    @property
    def policy_version(self) -> str:
        return "1.0.0"

    def assess(self, context: AssessmentContext) -> PolicyResult:
        raise AssessmentPolicyError("Simulated policy failure")


class UnexpectedErrorPolicy:
    """Test policy that raises an unexpected programming error."""

    @property
    def policy_id(self) -> str:
        return "TEST-ERROR"

    @property
    def policy_version(self) -> str:
        return "1.0.0"

    def assess(self, context: AssessmentContext) -> PolicyResult:
        raise RuntimeError("Unexpected programming error")


class SecondSuccessfulPolicy:
    """Test policy used to verify multiple-policy execution."""

    @property
    def policy_id(self) -> str:
        return "TEST-SECOND"

    @property
    def policy_version(self) -> str:
        return "1.0.0"

    def assess(self, context: AssessmentContext) -> PolicyResult:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "execution_status": "completed",
            "findings": [],
            "limitations": [],
        }


def test_orchestrator_runs_registered_a1_policy(
    successful_context: AssessmentContext,
) -> None:
    registry = AssessmentPolicyRegistry()
    registry.register(A1TLSConfigurationPolicy())

    orchestrator = AssessmentOrchestrator(registry)

    result = orchestrator.run_assess(
        context=successful_context,
        assessment_run_id="run-001",
        created_at="2026-10-22T12:00:00Z",
    )

    assert "A1" in result["assessments"]

    a1_result = result["assessments"]["A1"]

    assert a1_result["policy_id"] == "A1"
    assert a1_result["execution_status"] == "completed"
    assert len(a1_result["findings"]) == 4


def test_orchestrator_includes_assessment_run_metadata(
    successful_context: AssessmentContext,
) -> None:
    registry = AssessmentPolicyRegistry()
    registry.register(A1TLSConfigurationPolicy())

    orchestrator = AssessmentOrchestrator(registry)

    result = orchestrator.run_assess(
        context=successful_context,
        assessment_run_id="run-002",
        created_at="2026-10-22T12:00:00Z",
        schema_version="1.0",
    )

    assert result["schema_version"] == "1.0"
    assert result["assessment_run_id"] == "run-002"
    assert result["created_at"] == "2026-10-22T12:00:00Z"
    assert result["domain"] == successful_context["domain"]
    assert result["methodology_version"] == (successful_context["methodology_version"])
    assert result["evidence"] == successful_context["tls"]


def test_orchestrator_records_expected_policy_failure(
    successful_context: AssessmentContext,
) -> None:
    registry = AssessmentPolicyRegistry()
    registry.register(FailingPolicy())

    orchestrator = AssessmentOrchestrator(registry)

    result = orchestrator.run_assess(
        context=successful_context,
        assessment_run_id="run-003",
        created_at="2026-10-22T12:00:00Z",
    )

    failed_result = result["assessments"]["TEST-FAIL"]

    assert failed_result["policy_id"] == "TEST-FAIL"
    assert failed_result["policy_version"] == "1.0.0"
    assert failed_result["execution_status"] == "failed"
    assert failed_result["findings"] == []
    assert len(failed_result["limitations"]) == 1
    assert "Simulated policy failure" in failed_result["limitations"][0]


def test_orchestrator_propagates_unexpected_errors(
    successful_context: AssessmentContext,
) -> None:
    registry = AssessmentPolicyRegistry()
    registry.register(UnexpectedErrorPolicy())

    orchestrator = AssessmentOrchestrator(registry)

    with pytest.raises(
        RuntimeError,
        match="Unexpected programming error",
    ):
        orchestrator.run_assess(
            context=successful_context,
            assessment_run_id="run-004",
            created_at="2026-10-22T12:00:00Z",
        )


def test_orchestrator_runs_multiple_registered_policies(
    successful_context: AssessmentContext,
) -> None:
    registry = AssessmentPolicyRegistry()
    registry.register(A1TLSConfigurationPolicy())
    registry.register(SecondSuccessfulPolicy())

    orchestrator = AssessmentOrchestrator(registry)

    result = orchestrator.run_assess(
        context=successful_context,
        assessment_run_id="run-005",
        created_at="2026-10-22T12:00:00Z",
    )

    assessments = result["assessments"]

    assert set(assessments) == {"A1", "TEST-SECOND"}
    assert assessments["A1"]["execution_status"] == "completed"
    assert assessments["TEST-SECOND"]["execution_status"] == "completed"
