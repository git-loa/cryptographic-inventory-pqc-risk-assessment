"""Tests for the assessment policy registry."""

from dataclasses import dataclass

import pytest

from pqc_inventory.assessment.models import AssessmentContext, PolicyResult
from pqc_inventory.assessment.registry import AssessmentPolicyRegistry


@dataclass(frozen=True)
class StubPolicy:
    """Minimal assessment policy for registry tests."""

    policy_id: str
    policy_version: str = "1.0"
    policy_name: str = "Stub policy"
    policy_description: str = "Policy used in registry tests."

    def assess(self, context: AssessmentContext) -> PolicyResult:
        """Return a minimal valid policy result."""
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "execution_status": "completed",
            "findings": [],
            "limitations": [],
        }


def test_register_and_retrieve_policy() -> None:
    """A registered policy can be retrieved by its identifier."""
    registry = AssessmentPolicyRegistry()
    policy = StubPolicy(policy_id="TEST-1")

    registry.register(policy)

    assert registry.get("TEST-1") is policy


def test_all_returns_registered_policies() -> None:
    """The registry returns all registered policies."""
    registry = AssessmentPolicyRegistry()
    first = StubPolicy(policy_id="TEST-1")
    second = StubPolicy(policy_id="TEST-2")

    registry.register(first)
    registry.register(second)

    assert registry.all() == (first, second)


def test_register_rejects_duplicate_policy_id() -> None:
    """A duplicate identifier is rejected."""
    registry = AssessmentPolicyRegistry()
    original = StubPolicy(policy_id="TEST-1")
    duplicate = StubPolicy(
        policy_id="TEST-1",
        policy_name="Duplicate policy",
    )

    registry.register(original)

    with pytest.raises(ValueError):
        registry.register(duplicate)

    assert registry.get("TEST-1") is original
    assert registry.all() == (original,)


def test_get_raises_key_error_for_unknown_policy() -> None:
    """Retrieving an unknown policy raises KeyError."""
    registry = AssessmentPolicyRegistry()

    with pytest.raises(KeyError):
        registry.get("UNKNOWN")


def test_empty_registry_returns_empty_tuple() -> None:
    """A new registry contains no policies."""
    registry = AssessmentPolicyRegistry()

    assert not registry.all()
