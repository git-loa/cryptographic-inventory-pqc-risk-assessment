"""Tests for structured A1 assessment integration."""

from src.scanner.a1_assessment import assess_a1_configuration
from src.scanner.assessment import assess_tls_results


def test_a1_assessment_classifies_all_four_dimensions():
    tls_result = {
        "domain": "example.com",
        "port": 443,
        "tls_version": "TLSv1.3",
        "cipher_suite": "TLS_AES_256_GCM_SHA384",
        "public_key_algorithm": "ML-DSA",
        "certificate_signature_algorithm_oid": "2.16.840.1.101.3.4.3.18",
        "certificate_signature_hash_algorithm": None,
    }

    result = assess_a1_configuration(tls_result)

    assert set(result) == {
        "tls_version",
        "cipher_suite",
        "public_key_algorithm",
        "certificate_signature",
    }
    assert result["tls_version"]["classification"] == "acceptable"
    assert result["cipher_suite"]["classification"] == "acceptable"
    assert result["public_key_algorithm"]["classification"] == "acceptable"
    assert result["certificate_signature"]["classification"] == "acceptable"
    assert all(finding["reason"] for finding in result.values())


def test_a1_assessment_keeps_missing_evidence_unknown():
    tls_result = {"domain": "unavailable.example", "port": 443, "error": "connect failed"}

    result = assess_a1_configuration(tls_result)

    assert all(finding["classification"] == "unknown" for finding in result.values())
    assert all(finding["observed"] == "unknown" for finding in result.values())


def test_a1_findings_are_integrated_into_combined_assessment():
    tls_result = {
        "domain": "example.org",
        "port": 443,
        "tls_version": "TLSv1.2",
        "cipher_suite": "ECDHE-RSA-AES128-GCM-SHA256",
        "public_key_algorithm": "RSA",
        "certificate_signature_algorithm_oid": "1.2.840.113549.1.1.11",
        "certificate_signature_hash_algorithm": "sha256",
    }

    _, reports = assess_tls_results([tls_result])

    assert len(reports) == 1
    assert "a1" in reports[0]
    assert reports[0]["a1"] == assess_a1_configuration(tls_result)
    assert reports[0]["a1"]["tls_version"]["classification"] == "acceptable_with_review"
    assert reports[0]["a1"]["cipher_suite"]["classification"] == "acceptable"
    assert reports[0]["a1"]["public_key_algorithm"]["classification"] == "acceptable_with_review"
    assert reports[0]["a1"]["certificate_signature"]["classification"] == "acceptable_with_review"
