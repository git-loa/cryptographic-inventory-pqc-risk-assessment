"""
Unit tests for the PQC scoring module.
"""

from src.scanner.pqc_scoring import score_pqc


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
    }

    result = score_pqc(tls_entry)

    assert result["domain"] == "weak.example"
    assert result["tls_score"] < 40
    assert result["pqc_risk"] == "high"
    assert isinstance(result["reasons"], list)
    assert any("Weak TLS version" in r for r in result["reasons"])
    assert any("Weak key size" in r for r in result["reasons"])
    assert any("RSA key exchange" in r for r in result["reasons"])
