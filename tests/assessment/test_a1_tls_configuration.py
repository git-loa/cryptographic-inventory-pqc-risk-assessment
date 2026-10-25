"""Tests for the A1 TLS configuration assessment policy."""

import pytest

from src.assessment.policies.a1_tls_configuration import (
    A1TLSConfigurationPolicy,
)


@pytest.fixture
def policy():
    """Return an A1 policy instance."""
    return A1TLSConfigurationPolicy()


@pytest.fixture
def assessment_context():
    """Provide minimal TLS evidence for A1 policy tests."""
    return {
        "domain": "example.com",
        "methodology_version": "1.0",
        "tls": {
            "scan_status": "completed",
            "tls_version": "TLSv1.3",
            "cipher_suite": "TLS_AES_128_GCM_SHA256",
            "public_key_algorithm": "RSA",
            "certificate_signature_algorithm_oid": ("1.2.840.113549.1.1.11"),
            "certificate_signature_hash_algorithm": "sha256",
        },
    }


# pylint: disable=redefined-outer-name


@pytest.mark.parametrize(
    ("scan_status", "expected_status", "expected_limitation"),
    [
        ("completed", "completed", None),
        (
            "partial",
            "partial",
            "The TLS scan completed partially; " "some evidence may be unavailable.",
        ),
        (
            "failed",
            "partial",
            "The TLS scan failed; " "available evidence may be incomplete.",
        ),
        (
            None,
            "partial",
            "The scan outcome is missing or unrecognized.",
        ),
        (
            "unexpected",
            "partial",
            "The scan outcome is missing or unrecognized.",
        ),
    ],
)
def test_execution_status_matches_scan_outcome(
    policy,
    assessment_context,
    scan_status,
    expected_status,
    expected_limitation,
):
    """Map collection scan statuses to the expected A1 execution status."""
    assessment_context["tls"]["scan_status"] = scan_status

    result = policy.assess(assessment_context)

    assert result["execution_status"] == expected_status

    if expected_limitation is None:
        assert result["limitations"] == []
    else:
        assert expected_limitation in result["limitations"]


def test_completed_scan_produces_four_findings(
    policy,
    assessment_context,
):
    """A1 should produce one finding for each of its four dimensions."""
    result = policy.assess(assessment_context)

    assert len(result["findings"]) == 4

    assert [finding["rule_id"] for finding in result["findings"]] == [
        "A1.1",
        "A1.2",
        "A1.3",
        "A1.4",
    ]


def test_findings_include_rationale_and_evidence_references(
    policy,
    assessment_context,
):
    """Each A1 finding should explain its classification and evidence."""
    result = policy.assess(assessment_context)

    for finding in result["findings"]:
        assert finding["policy_id"] == "A1"
        assert finding["dimension"]
        assert finding["classification"]
        assert finding["rationale"]
        assert finding["evidence_references"]
