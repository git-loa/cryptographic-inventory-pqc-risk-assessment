"""Unit tests for the A1 TLS configuration assessment policy."""

import pytest

from src.assessment.models import AssessmentContext, AssessmentFinding
from src.assessment.policies.a1_classifiers import (
    classify_certificate_signature,
    classify_cipher_suite,
    classify_public_key_algorithm,
    classify_tls_version,
)
from src.assessment.policies.a1_tls_configuration import (
    A1TLSConfigurationPolicy,
)


def find_finding(
    findings: list[AssessmentFinding],
    dimension: str,
) -> AssessmentFinding:
    """Return the finding for a dimension or fail clearly."""
    for finding in findings:
        if finding["dimension"] == dimension:
            return finding

    pytest.fail(f"No finding found for dimension {dimension!r}")


def test_policy_metadata(a1_policy: A1TLSConfigurationPolicy) -> None:
    """Verify the policy exposes its expected identifier and version."""
    assert a1_policy.policy_id == "A1"
    assert a1_policy.policy_version == "1.0.0"


def test_successful_scan_produces_four_findings(
    a1_policy: A1TLSConfigurationPolicy,
    successful_context: AssessmentContext,
) -> None:
    """Verify a successful scan produces one finding per A1 dimension."""
    result = a1_policy.assess(successful_context)

    assert result["policy_id"] == "A1"
    assert result["policy_version"] == "1.0.0"
    assert result["execution_status"] == "completed"
    assert result["limitations"] == []
    assert len(result["findings"]) == 4

    assert {finding["rule_id"] for finding in result["findings"]} == {
        "A1.1",
        "A1.2",
        "A1.3",
        "A1.4",
    }

    assert {finding["dimension"] for finding in result["findings"]} == {
        "tls_version",
        "cipher_suite",
        "public_key_algorithm",
        "certificate_signature",
    }


def test_tls_version_and_cipher_suite_are_acceptable(
    a1_policy: A1TLSConfigurationPolicy,
    successful_context: AssessmentContext,
) -> None:
    """Verify representative TLS 1.3 evidence receives expected classifications."""
    result = a1_policy.assess(successful_context)

    tls_version_finding = find_finding(result["findings"], "tls_version")
    cipher_suite_finding = find_finding(result["findings"], "cipher_suite")

    assert tls_version_finding["classification"] == "acceptable"
    assert cipher_suite_finding["classification"] == "acceptable"


def test_findings_include_evidence_and_rationale(
    a1_policy: A1TLSConfigurationPolicy,
    successful_context: AssessmentContext,
) -> None:
    """Verify findings include traceable evidence and classification rationale."""
    result = a1_policy.assess(successful_context)

    for finding in result["findings"]:
        assert finding["evidence_references"]
        assert finding["rationale"]
        assert finding["rule_id"]
        assert finding["finding_id"].startswith("A1-")


def test_missing_evidence_is_classified_as_unknown(
    a1_policy: A1TLSConfigurationPolicy,
) -> None:
    """Verify missing TLS and certificate metadata is handled safely."""
    context: AssessmentContext = {
        "domain": "example.com",
        "methodology_version": "1.0",
        "tls": {
            "domain": "example.com",
            "port": 443,
            "scan_status": "success",
        },
    }

    result = a1_policy.assess(context)

    assert result["execution_status"] == "completed"
    assert len(result["findings"]) == 4

    for finding in result["findings"]:
        assert finding["classification"] == "unknown"
        assert finding["observed_value"] is None


def test_failed_scan_returns_partial_status(
    a1_policy: A1TLSConfigurationPolicy,
) -> None:
    """Verify a failed scan produces a partial result and a limitation."""
    context: AssessmentContext = {
        "domain": "example.com",
        "methodology_version": "1.0",
        "tls": {
            "domain": "example.com",
            "port": 443,
            "scan_status": "failed",
            "error": "Connection timed out",
        },
    }

    result = a1_policy.assess(context)

    assert result["execution_status"] == "partial"
    assert len(result["findings"]) == 4
    assert result["limitations"]
    assert any(
        "scan failed" in limitation.lower() for limitation in result["limitations"]
    )


@pytest.mark.parametrize("scan_status", [None, "unexpected"])
def test_unclear_scan_status_returns_partial(
    a1_policy: A1TLSConfigurationPolicy,
    successful_context: AssessmentContext,
    scan_status: str | None,
) -> None:
    """Verify missing or unrecognized scan status is reported as partial."""
    context: AssessmentContext = {
        **successful_context,
        "tls": {
            **successful_context["tls"],
            "scan_status": scan_status,
        },
    }

    result = a1_policy.assess(context)

    assert result["execution_status"] == "partial"
    assert result["limitations"]
    assert any(
        "missing or unrecognized" in limitation.lower()
        for limitation in result["limitations"]
    )


@pytest.mark.parametrize(
    ("tls_version", "expected_classification"),
    [
        ("TLSv1.3", "acceptable"),
        ("tlsv1.3", "acceptable"),
        (" TLSv1.3 ", "acceptable"),
        ("TLSv1.2", "acceptable_with_review"),
        ("TLSv1.0", "unacceptable"),
        ("TLSv1.1", "unacceptable"),
        ("SSLv2", "unacceptable"),
        ("SSLv3", "unacceptable"),
        (None, "unknown"),
        ("", "unknown"),
        ("TLSv9.9", "unknown"),
    ],
)
def test_tls_version_classification(
    tls_version: str | None,
    expected_classification: str,
) -> None:
    """Verify TLS versions follow the A1.1 classification rules."""
    result = classify_tls_version(tls_version)

    assert result["classification"] == expected_classification
    assert result["dimension"] == "tls_version"
    assert result["reason"]


@pytest.mark.parametrize(
    ("cipher_suite", "tls_version", "expected_classification"),
    [
        (
            "TLS_AES_128_GCM_SHA256",
            "TLSv1.3",
            "acceptable",
        ),
        (
            "TLS_AES_256_GCM_SHA384",
            "TLSv1.3",
            "acceptable",
        ),
        (
            "TLS_CHACHA20_POLY1305_SHA256",
            "TLSv1.3",
            "acceptable",
        ),
        (
            "TLS_AES_128_CCM_8_SHA256",
            "TLSv1.3",
            "acceptable_with_review",
        ),
        (
            "TLS_RSA_WITH_AES_128_GCM_SHA256",
            "TLSv1.2",
            "acceptable_with_review",
        ),
        (
            "ECDHE-RSA-AES128-GCM-SHA256",
            "TLSv1.2",
            "acceptable",
        ),
        (
            "ECDHE-RSA-AES128-SHA",
            "TLSv1.2",
            "acceptable_with_review",
        ),
        (
            "TLS_RSA_WITH_RC4_128_SHA",
            "TLSv1.2",
            "unacceptable",
        ),
        (
            "TLS_RSA_WITH_3DES_EDE_CBC_SHA",
            "TLSv1.2",
            "unacceptable",
        ),
        (
            "UNKNOWN_CIPHER_SUITE",
            "TLSv1.3",
            "unknown",
        ),
        (
            "TLS_AES_128_GCM_SHA256",
            None,
            "unknown",
        ),
        (
            None,
            "TLSv1.3",
            "unknown",
        ),
    ],
)
def test_cipher_suite_classification(
    cipher_suite: str | None,
    tls_version: str | None,
    expected_classification: str,
) -> None:
    """Verify cipher suites follow the A1.2 classification rules."""
    result = classify_cipher_suite(cipher_suite, tls_version)

    assert result["classification"] == expected_classification
    assert result["dimension"] == "cipher_suite"
    assert result["reason"]


@pytest.mark.parametrize(
    ("algorithm", "expected_classification"),
    [
        ("ML-DSA", "acceptable"),
        ("RSA", "acceptable_with_review"),
        ("EC", "acceptable_with_review"),
        ("ED25519", "acceptable_with_review"),
        ("ED448", "acceptable_with_review"),
        ("DSA", "unacceptable"),
        ("UNKNOWN-ALGORITHM", "unknown"),
        (None, "unknown"),
        ("", "unknown"),
    ],
)
def test_public_key_algorithm_classification(
    algorithm: str | None,
    expected_classification: str,
) -> None:
    """Verify public-key algorithms follow the A1.3 classification rules."""
    result = classify_public_key_algorithm(algorithm)

    assert result["classification"] == expected_classification
    assert result["dimension"] == "public_key_algorithm"
    assert result["reason"]


@pytest.mark.parametrize(
    ("signature_oid", "hash_algorithm", "expected_classification"),
    [
        # Deprecated SHA-1 signature algorithms.
        ("1.2.840.113549.1.1.5", "sha1", "unacceptable"),
        ("1.2.840.10045.4.1", "sha1", "unacceptable"),
        # Recognized classical signature algorithms.
        ("1.2.840.113549.1.1.11", "sha256", "acceptable_with_review"),
        ("1.2.840.113549.1.1.12", "sha384", "acceptable_with_review"),
        ("1.2.840.10045.4.3.2", "sha256", "acceptable_with_review"),
        ("1.3.101.112", None, "acceptable_with_review"),
        # RSA-PSS requires recognized hash evidence.
        ("1.2.840.113549.1.1.10", "sha256", "acceptable_with_review"),
        ("1.2.840.113549.1.1.10", "sha384", "acceptable_with_review"),
        ("1.2.840.113549.1.1.10", None, "unknown"),
        ("1.2.840.113549.1.1.10", "sha1", "unknown"),
        # Recognized post-quantum signature OIDs.
        ("2.16.840.1.101.3.4.3.17", None, "acceptable"),
        ("2.16.840.1.101.3.4.3.18", None, "acceptable"),
        ("2.16.840.1.101.3.4.3.19", None, "acceptable"),
        # Missing or unrecognized signature evidence.
        (None, None, "unknown"),
        ("", None, "unknown"),
        ("1.2.3.4.5.6", None, "unknown"),
    ],
)
def test_certificate_signature_classification(
    signature_oid: str | None,
    hash_algorithm: str | None,
    expected_classification: str,
) -> None:
    """Verify certificate signatures follow the A1.4 classification rules."""
    result = classify_certificate_signature(signature_oid, hash_algorithm)

    assert result["classification"] == expected_classification
    assert result["dimension"] == "certificate_signature"
    assert result["reason"]
