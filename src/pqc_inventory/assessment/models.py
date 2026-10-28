"""
Shared data models for cryptographic assessment.

These models define the contracts used by assessment policies,
the assessment orchestrator, and reporting components.
"""

from typing import Literal, TypedDict

from pqc_inventory.collection.models import TLSScanResult

AssessmentClassification = Literal[
    "acceptable",
    "acceptable_with_review",
    "unacceptable",
    "unknown",
]

PolicyExecutionStatus = Literal[
    "completed",
    "partial",
    "not_assessed",
    "failed",
]


class AssessmentFinding(TypedDict):
    """One evidence-linked finding produced by an assessment policy."""

    finding_id: str
    policy_id: str
    dimension: str
    observed_value: str | None
    classification: AssessmentClassification
    rule_id: str
    rationale: str
    evidence_references: list[str]


class PolicyResult(TypedDict):
    """The result of executing one assessment policy."""

    policy_id: str
    policy_version: str
    execution_status: PolicyExecutionStatus
    findings: list[AssessmentFinding]
    limitations: list[str]


class AssessmentContext(TypedDict):
    """Evidence and methodology context supplied to an assessment policy."""

    domain: str
    tls: TLSScanResult
    methodology_version: str


class AssessmentRun(TypedDict):
    """A complete assessment run for a single target."""

    schema_version: str
    assessment_run_id: str
    domain: str
    created_at: str
    methodology_version: str
    evidence: TLSScanResult
    assessments: dict[str, PolicyResult]
