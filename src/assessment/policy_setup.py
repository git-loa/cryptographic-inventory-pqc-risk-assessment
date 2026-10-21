"""Configure the assessment registry with available policies."""

from src.assessment.policies.a1_tls_configuration import (
    A1TLSConfigurationPolicy,
)
from src.assessment.registry import AssessmentPolicyRegistry


def create_default_registry() -> AssessmentPolicyRegistry:
    """Create a registry containing the currently implemented policies."""
    registry = AssessmentPolicyRegistry()

    registry.register(A1TLSConfigurationPolicy())

    return registry
