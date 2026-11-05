"""
Shared data models for cryptographic assessment.

These models define the contracts used by assessment policies,
the assessment orchestrator, and reporting components.
"""

from __future__ import annotations

from dataclasses import dataclass
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


# ---------------------------------------------------------------------------
# JSON-compatible policy metadata records
# ---------------------------------------------------------------------------


class PolicyReferenceRecord(TypedDict):
    """JSON-compatible representation of a policy reference."""

    reference_id: str
    title: str
    publisher: str
    url: str
    relevance: str
    version: str | None


class PolicyRuleRecord(TypedDict):
    """JSON-compatible representation of an assessment rule."""

    rule_id: str
    name: str
    description: str
    dimension: str
    evaluation_summary: str
    references: list[PolicyReferenceRecord]


class PolicyMetadataRecord(TypedDict):
    """JSON-compatible snapshot of assessment policy metadata."""

    policy_id: str
    name: str
    version: str
    description: str
    scope: list[str]
    rules: list[PolicyRuleRecord]
    references: list[PolicyReferenceRecord]


# ---------------------------------------------------------------------------
# Immutable policy metadata models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyReference:
    """Describes an external reference supporting a policy or rule."""

    reference_id: str
    title: str
    publisher: str
    url: str
    relevance: str
    version: str | None = None


@dataclass(frozen=True)
class PolicyRule:
    """Describes an individual assessment rule within a policy."""

    rule_id: str
    name: str
    description: str
    dimension: str
    evaluation_summary: str
    references: tuple[PolicyReference, ...] = ()


@dataclass(frozen=True)
class PolicyMetadata:
    """Provides descriptive and reference metadata for an assessment policy."""

    policy_id: str
    name: str
    version: str
    description: str
    scope: tuple[str, ...]
    rules: tuple[PolicyRule, ...]
    references: tuple[PolicyReference, ...] = ()

    def to_record(self) -> PolicyMetadataRecord:
        """Convert policy metadata into a JSON-compatible record."""

        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "scope": list(self.scope),
            "rules": [
                {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "description": rule.description,
                    "dimension": rule.dimension,
                    "evaluation_summary": rule.evaluation_summary,
                    "references": [
                        {
                            "reference_id": reference.reference_id,
                            "title": reference.title,
                            "publisher": reference.publisher,
                            "url": reference.url,
                            "relevance": reference.relevance,
                            "version": reference.version,
                        }
                        for reference in rule.references
                    ],
                }
                for rule in self.rules
            ],
            "references": [
                {
                    "reference_id": reference.reference_id,
                    "title": reference.title,
                    "publisher": reference.publisher,
                    "url": reference.url,
                    "relevance": reference.relevance,
                    "version": reference.version,
                }
                for reference in self.references
            ],
        }


# ---------------------------------------------------------------------------
# Assessment execution models
# ---------------------------------------------------------------------------


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


class PolicyExecutionRecord(TypedDict):
    """Combines a policy metadata snapshot with its execution result."""

    metadata: PolicyMetadataRecord
    result: PolicyResult


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
    assessments: dict[str, PolicyExecutionRecord]
