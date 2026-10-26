"""Application service for TLS evidence assessment."""

import uuid
from pathlib import Path
from typing import Sequence

from pqc_inventory.application.evidence_validator import EvidenceValidator
from pqc_inventory.assessment.models import AssessmentContext, AssessmentRun
from pqc_inventory.assessment.orchestrator import AssessmentOrchestrator
from pqc_inventory.assessment.policy_setup import create_default_registry
from pqc_inventory.assessment.registry import AssessmentPolicyRegistry
from pqc_inventory.collection.models import TLSScanResult
from pqc_inventory.collection.tls_utils import utc_now
from pqc_inventory.storage.json_repository import JSONRepository


class AssessmentService:
    """Coordinate TLS evidence validation and security assessment."""

    def __init__(
        self,
        repository: JSONRepository | None = None,
        registry: AssessmentPolicyRegistry | None = None,
        methodology_version: str = "1.0",
    ) -> None:
        """Initialize the assessment service and its dependencies."""
        self._repository = repository or JSONRepository()
        self._registry = registry or create_default_registry()
        self._methodology_version = methodology_version

    def assess_evidence(
        self,
        evidence: object,
        policy_ids: Sequence[str] | None = None,
    ) -> list[AssessmentRun]:
        """Validate evidence and assess each TLS scan result.

        Args:
            evidence: One TLS evidence record or a list of records.
            policy_ids: Optional identifiers of policies to execute.

        Returns:
            One assessment run for each validated TLS evidence record.

        Raises:
            ValueError: If evidence is invalid or no policies are selected.
            KeyError: If a requested policy is not registered.
        """
        validated_evidence = EvidenceValidator.validate(evidence)
        registry = self._select_registry(policy_ids)
        orchestrator = AssessmentOrchestrator(registry)

        return [
            self._assess_single_evidence(
                tls_evidence=tls_evidence,
                orchestrator=orchestrator,
            )
            for tls_evidence in validated_evidence
        ]

    def assess_file(
        self,
        input_path: str | Path,
        output_path: str | Path,
        policy_ids: Sequence[str] | None = None,
    ) -> list[AssessmentRun]:
        """Load TLS evidence, assess it, and save the resulting reports.

        Args:
            input_path: Path to the input TLS evidence JSON file.
            output_path: Path where assessment results will be saved.
            policy_ids: Optional identifiers of policies to execute.

        Returns:
            The generated assessment runs.
        """
        evidence = self._repository.load_json(input_path)

        assessment_runs = self.assess_evidence(
            evidence=evidence,
            policy_ids=policy_ids,
        )

        self._repository.save_json(
            output_path,
            assessment_runs,
        )

        return assessment_runs

    def _assess_single_evidence(
        self,
        tls_evidence: TLSScanResult,
        orchestrator: AssessmentOrchestrator,
    ) -> AssessmentRun:
        """Execute the selected policies against one TLS evidence record."""
        context: AssessmentContext = {
            "domain": tls_evidence["target"],
            "tls": tls_evidence,
            "methodology_version": self._methodology_version,
        }

        return orchestrator.run_assess(
            context=context,
            assessment_run_id=str(uuid.uuid4()),
            created_at=utc_now(),
        )

    def _select_registry(
        self,
        policy_ids: Sequence[str] | None,
    ) -> AssessmentPolicyRegistry:
        """Build a registry containing the requested policies."""
        if policy_ids is None:
            return self._registry

        if not policy_ids:
            raise ValueError("At least one assessment policy must be selected.")

        selected_registry = AssessmentPolicyRegistry()

        for policy_id in policy_ids:
            policy = self._registry.get(policy_id)
            selected_registry.register(policy)

        return selected_registry
