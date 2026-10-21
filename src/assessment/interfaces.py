"""
Interfaces defining the contract for assessment policies.
"""

from typing import Protocol

from src.assessment.models import AssessmentContext, PolicyResult


class AssessmentPolicy(Protocol):
    """
    Contract that every assessment policy must implement.

    Policies evaluate supplied evidence and return standardized results.
    They must not perform network scans or persist results themselves.
    """

    # pylint: disable=unnecessary-ellipsis
    @property
    def policy_id(self) -> str:
        """Return the stable identifier for this policy."""
        ...

    @property
    def policy_version(self) -> str:
        """Return the version of this policy's implementation."""
        ...

    def assess(self, context: AssessmentContext) -> PolicyResult:
        """
        Evaluate the supplied evidence.

        Args:
            context: Evidence and methodology metadata for the target.

        Returns:
            Structured findings, execution status, and limitations.
        """
        ...


class AssessmentPolicyError(Exception):
    """Raised when an assessment policy cannot complete its evaluation."""
