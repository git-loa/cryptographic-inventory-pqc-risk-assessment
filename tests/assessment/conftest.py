"""
Unified pytest fixtures for A1 policy
"""

import pytest

from src.assessment.models import AssessmentContext
from src.assessment.policies.a1_tls_configuration import A1TLSConfigurationPolicy


@pytest.fixture
def a1_policy() -> A1TLSConfigurationPolicy:
    """Return a fresh A1 policy instance."""
    return A1TLSConfigurationPolicy()


@pytest.fixture
def successful_context() -> AssessmentContext:
    """Provide representative evidence from a successful TLS scan."""
    return {
        "domain": "example.com",
        "methodology_version": "1.0",
        "tls": {
            "domain": "example.com",
            "port": 443,
            "tls_version": "TLSv1.3",
            "cipher_suite": "TLS_AES_128_GCM_SHA256",
            "public_key_algorithm": "RSA",
            "certificate_signature_algorithm_oid": "1.2.840.113549.1.1.11",
            "certificate_signature_hash_algorithm": "sha256",
            "scan_status": "success",
        },
    }
