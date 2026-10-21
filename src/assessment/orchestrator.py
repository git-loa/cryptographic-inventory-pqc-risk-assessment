"""Orchestrate execution of registered assessment policies."""

from src.assessment.models import (
    AssessmentContext,
    AssessmentRun,
    PolicyResult,
)
from src.assessment.registry import AssessmentPolicyRegistry
from src.assessment.interfaces import AssessmentPolicyError


# pylint: disable=too-few-public-methods
class AssessmentOrchestrator:
    """Execute registered policies and collect their results."""

    def __init__(self, registry: AssessmentPolicyRegistry) -> None:
        self._registry = registry

    def run_assess(
        self,
        context: AssessmentContext,
        assessment_run_id: str,
        created_at: str,
        schema_version: str = "1.0",
    ) -> AssessmentRun:
        """Execute all registered policies for one assessment context."""
        assessments: dict[str, PolicyResult] = {}

        for policy in self._registry.all():
            try:
                result = policy.assess(context=context)
            except AssessmentPolicyError as exc:
                result = {
                    "policy_id": policy.policy_id,
                    "policy_version": policy.policy_version,
                    "execution_status": "failed",
                    "findings": [],
                    "limitations": [
                        f"Policy execution failed: {type(exc).__name__}: {exc}"
                    ],
                }
            assessments[policy.policy_id] = result

        return {
            "schema_version": schema_version,
            "assessment_run_id": assessment_run_id,
            "domain": context["domain"],
            "created_at": created_at,
            "methodology_version": context["methodology_version"],
            "evidence": context["tls"],
            "assessments": assessments,
        }
