"""
Test to verify assessment registry correctly manages policies
"""

import pytest

from src.assessment.policies.a1_tls_configuration import (
    A1TLSConfigurationPolicy,
)
from src.assessment.registry import AssessmentPolicyRegistry


# pylint: disable = missing-function-docstring
def test_register_and_get_policy() -> None:
    registry = AssessmentPolicyRegistry()
    policy = A1TLSConfigurationPolicy()

    registry.register(policy)

    assert registry.get("A1") is policy


def test_register_duplicate_policy_id_raises_value_error() -> None:
    registry = AssessmentPolicyRegistry()

    first_policy = A1TLSConfigurationPolicy()
    second_policy = A1TLSConfigurationPolicy()

    registry.register(first_policy)

    with pytest.raises(ValueError):
        registry.register(second_policy)


def test_get_unknown_policy_raises_key_error() -> None:
    registry = AssessmentPolicyRegistry()

    with pytest.raises(KeyError):
        registry.get("UNKNOWN")


def test_all_returns_registered_policies() -> None:
    registry = AssessmentPolicyRegistry()
    policy = A1TLSConfigurationPolicy()

    registry.register(policy)

    policies = registry.all()

    assert len(policies) == 1
    assert policies[0] is policy


def test_all_returns_empty_tuple_when_no_policies_registered() -> None:
    registry = AssessmentPolicyRegistry()

    policies = registry.all()

    # pylint: disable = use-implicit-booleaness-not-comparison
    assert policies == ()
