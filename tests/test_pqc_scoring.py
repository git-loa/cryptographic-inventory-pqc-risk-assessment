"""
Unit tests for the PQC scoring module.
"""

import pytest

from src.scanner.pqc_scoring import (
    classify_tls_version,
    classify_cipher_suite,
    classify_public_key_algorithm,
    classify_certificate_signature,
)
from src.scanner.pqc_scoring import score_pqc


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("TLSv1.3", "acceptable"),
        ("TLSv1.2", "acceptable_with_review"),
        ("TLSv1.1", "unacceptable"),
        ("TLSv1.0", "unacceptable"),
        ("SSLv2", "unacceptable"),
        ("SSLv3", "unacceptable"),
        (None, "unknown"),
        ("TLSv9.0", "unknown"),
    ],
)
def test_classify_tls_version(version, expected):
    """TLS version classification follows the A1.1 policy."""

    result = classify_tls_version(version)

    assert result["classification"] == expected
    assert result["dimension"] == "tls_version"
    assert result["reason"]


@pytest.mark.parametrize(
    ("suite", "version", "strength", "expected"),
    [
        (
            "TLS_AES_256_GCM_SHA384",
            "TLSv1.3",
            256,
            "acceptable",
        ),
        (
            "TLS_CHACHA20_POLY1305_SHA256",
            "TLSv1.3",
            256,
            "acceptable",
        ),
        (
            "ECDHE-RSA-AES128-GCM-SHA256",
            "TLSv1.2",
            128,
            "acceptable",
        ),
        (
            "ECDHE-RSA-AES128-SHA",
            "TLSv1.2",
            128,
            "unknown",
        ),
        (
            "RSA_WITH_RC4_128_SHA",
            "TLSv1.2",
            128,
            "unacceptable",
        ),
        (
            "NULL_WITH_NULL_NULL",
            "TLSv1.2",
            0,
            "unacceptable",
        ),
        (
            "ECDHE-RSA-AES128-CBC-SHA256",
            "TLSv1.2",
            128,
            "acceptable_with_review",
        ),
        (
            "UNRECOGNIZED_SUITE",
            "TLSv1.2",
            128,
            "unknown",
        ),
        (
            None,
            "TLSv1.2",
            None,
            "unknown",
        ),
    ],
)
def test_classify_cipher_suite(suite, version, strength, expected):
    """Cipher-suite classification follows the initial A1.2 policy."""

    result = classify_cipher_suite(suite, version, strength)

    assert result["classification"] == expected
    assert result["dimension"] == "cipher_suite"
    assert result["reason"]


@pytest.mark.parametrize(
    ("algorithm", "expected"),
    [
        ("RSA", "acceptable_with_review"),
        ("EC", "acceptable_with_review"),
        ("Ed25519", "acceptable_with_review"),
        ("Ed448", "acceptable_with_review"),
        ("DSA", "unacceptable"),
        ("ML-DSA", "acceptable"),
        (None, "unknown"),
        ("", "unknown"),
        ("UnknownKeyType", "unknown"),
    ],
)
def test_classify_public_key_algorithm(algorithm, expected):
    """Public-key algorithm classification follows the initial A1.3 policy."""
    result = classify_public_key_algorithm(algorithm)

    assert result["dimension"] == "public_key_algorithm"
    assert result["classification"] == expected
    assert result["reason"]


@pytest.mark.parametrize(
    ("oid", "hash_name", "expected"),
    [
        (
            "1.2.840.113549.1.1.11",
            "sha256",
            "acceptable_with_review",
        ),
        (
            "1.2.840.10045.4.3.2",
            "sha256",
            "acceptable_with_review",
        ),
        (
            "1.3.101.112",
            None,
            "acceptable_with_review",
        ),
        (
            "1.2.840.113549.1.1.5",
            "sha1",
            "unacceptable",
        ),
        (
            "1.2.840.113549.1.1.10",
            "sha384",
            "acceptable_with_review",
        ),
        (
            "1.2.840.113549.1.1.10",
            None,
            "unknown",
        ),
        (
            "2.16.840.1.101.3.4.3.18",
            None,
            "acceptable",
        ),
        (None, None, "unknown"),
        ("1.2.3.4.5", None, "unknown"),
    ],
)
def test_classify_certificate_signature(oid, hash_name, expected):
    """Certificate signature classification follows the A1.4 policy."""

    result = classify_certificate_signature(oid, hash_name)

    assert result["dimension"] == "certificate_signature"
    assert result["classification"] == expected
    assert result["reason"]


# ---------------------------------------------------------------
# ---------------------------------------------------------------------


def test_pqc_scoring_low_risk():
    """
    Strong TLS configuration should produce low PQC risk.
    """
    tls_entry = {
        "domain": "microsoft.com",
        "tls_version": "TLSv1.3",
        "cipher_suite": "TLS_AES_256_GCM_SHA384",
        "cipher_strength": 256,
        "key_size": 4096,
        "public_key_algorithm": "RSA",
    }

    result = score_pqc(tls_entry)

    assert result["domain"] == "microsoft.com"
    assert result["tls_score"] >= 70
    assert result["pqc_risk"] == "low"
    assert isinstance(result["reasons"], list)


def test_pqc_scoring_medium_risk():
    """
    Borderline key sizes or weaker cipher strength should produce medium PQC risk.
    """
    tls_entry = {
        "domain": "github.com",
        "tls_version": "TLSv1.3",
        "cipher_suite": "TLS_AES_128_GCM_SHA256",
        "cipher_strength": 128,
        "key_size": 256,
    }

    result = score_pqc(tls_entry)

    assert result["domain"] == "github.com"
    assert 40 <= result["tls_score"] < 70
    assert result["pqc_risk"] == "medium"
    assert isinstance(result["reasons"], list)


def test_pqc_scoring_high_risk_missing_fields():
    """
    Missing TLS metadata should produce high PQC risk.
    """
    tls_entry = {
        "domain": "example.com",
        # No TLS fields → all scoring functions return 0
    }

    result = score_pqc(tls_entry)

    assert result["domain"] == "example.com"
    assert result["tls_score"] == 0
    assert result["pqc_risk"] == "high"
    assert isinstance(result["reasons"], list)
    assert len(result["reasons"]) >= 3  # version, key size, cipher suite


def test_pqc_scoring_high_risk_weak_values():
    """
    Weak TLS version + weak key size + weak cipher suite should produce high PQC risk.
    """
    tls_entry = {
        "domain": "weak.example",
        "tls_version": "TLSv1.0",
        "cipher_suite": "RSA_WITH_3DES_EDE_CBC_SHA",
        "cipher_strength": 56,
        "key_size": 512,
        "public_key_algorithm": "RSA",
    }

    result = score_pqc(tls_entry)

    assert result["domain"] == "weak.example"
    assert result["tls_score"] < 40
    assert result["pqc_risk"] == "high"
    assert isinstance(result["reasons"], list)
    assert any("Weak TLS version" in r for r in result["reasons"])
    assert any("Weak RSA key size" in r for r in result["reasons"])
    assert any("RSA key exchange" in r for r in result["reasons"])


# ----------
# New tests
# ----------


def test_256_bit_ec_key_is_not_flagged_as_weak_key_size():
    """A 256-bit EC key must not use RSA key-size thresholds."""
    tls_entry = {
        "domain": "example.com",
        "tls_version": "TLSv1.3",
        "cipher_suite": "TLS_AES_128_GCM_SHA256",
        "key_size": 256,
        "public_key_algorithm": "EC",
    }

    result = score_pqc(tls_entry)

    assert not any("Weak key size: 256 bits" in reason for reason in result["reasons"])
