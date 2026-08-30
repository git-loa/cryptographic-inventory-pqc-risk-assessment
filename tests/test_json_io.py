"""
Unit tests for the JSON IO module.
"""

from pathlib import Path
import tempfile

from src.scanner.json_io import (
    load_tls_results,
    load_pqc_scores,
    save_tls_results,
    save_pqc_scores,
)


def test_load_tls_results(tls_results):
    """
    Ensure TLS results fixture loads correctly.
    """
    assert isinstance(tls_results, list)
    assert len(tls_results) > 0

    first = tls_results[0]
    assert isinstance(first, dict)
    assert "domain" in first


def test_load_pqc_scores(pqc_scores):
    """
    Ensure PQC scores fixture loads correctly.
    """
    assert isinstance(pqc_scores, list)
    assert len(pqc_scores) > 0

    first = pqc_scores[0]
    assert isinstance(first, dict)

    # Updated to match actual PQC JSON structure
    assert "domain" in first
    assert "tls_score" in first
    assert "pqc_risk" in first
    assert "reasons" in first
    assert isinstance(first["reasons"], list)


def test_save_and_load_tls_results_roundtrip():
    """
    Test saving and loading TLS results to ensure data integrity.
    """
    sample_data = [
        # Minimal valid error entry
        {"domain": "example.com", "port": 443, "error": "DNS error: simulated"},
        # Minimal valid successful TLS entry
        {
            "domain": "github.com",
            "port": 443,
            "tls_version": "TLSv1.3",
            "cipher_suite": "TLS_AES_128_GCM_SHA256",
            "cipher_strength": 128,
            "key_size": 256,
            "not_before": "Jan  1 00:00:00 2026 GMT",
            "not_after": "Dec 31 23:59:59 2026 GMT",
            "certificate_subject": {"commonName": "github.com"},
            "certificate_issuer": {"commonName": "Example CA"},
        },
    ]

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "tls_results.json"

        save_tls_results(sample_data, path)
        loaded = load_tls_results(path)

        assert isinstance(loaded, list)
        assert loaded == sample_data


def test_save_and_load_pqc_scores_roundtrip():
    """
    Test saving and loading PQC scores to ensure data integrity.
    Updated to match actual PQCScore JSON structure.
    """
    sample_scores = [
        {
            "domain": "example.com",
            "tls_score": 0,
            "pqc_risk": "high",
            "reasons": ["No TLS version negotiated"],
        },
        {
            "domain": "github.com",
            "tls_score": 50,
            "pqc_risk": "medium",
            "reasons": ["Weak key size: 256 bits"],
        },
    ]

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pqc_scores.json"

        save_pqc_scores(sample_scores, path)
        loaded = load_pqc_scores(path)

        assert isinstance(loaded, list)
        assert loaded == sample_scores
