"""
Unit tests for TLS and PQC assessment orchestration.
"""

from src.scanner.assessment import assess_tls_results


def test_assessment_produces_scores_and_combined_reports():
    """Each TLS result should produce a score and a combined report."""

    tls_results = [
        {
            "domain": "example.com",
            "port": 443,
            "tls_version": "TLSv1.3",
            "cipher_suite": "TLS_AES_256_GCM_SHA384",
            "key_size": 4096,
        },
        {
            "domain": "google.com",
            "port": 443,
            "tls_version": "TLSv1.2",
            "cipher_suite": "TLS_AES_128_GCM_SHA256",
            "key_size": 2048,
        },
    ]

    pqc_scores, combined_reports = assess_tls_results(tls_results)

    assert len(pqc_scores) == len(tls_results)
    assert len(combined_reports) == len(tls_results)


def test_assessment_preserves_domain_association():
    """Each score must belong to the TLS result being assessed."""

    tls_results = [
        {
            "domain": "example.com",
            "port": 443,
            "tls_version": "TLSv1.3",
            "cipher_suite": "TLS_AES_256_GCM_SHA384",
            "key_size": 4096,
        },
        {
            "domain": "google.com",
            "port": 443,
            "tls_version": "TLSv1.2",
            "cipher_suite": "TLS_AES_128_GCM_SHA256",
            "key_size": 2048,
        },
    ]

    pqc_scores, combined_reports = assess_tls_results(tls_results)

    for tls, score, combined in zip(
        tls_results,
        pqc_scores,
        combined_reports,
    ):
        assert score["domain"] == tls["domain"]
        assert combined["domain"] == tls["domain"]
        assert combined["tls"] == tls
        assert combined["pqc"] == score


def test_assessment_preserves_input_order():
    """The assessment should preserve the original TLS result order."""

    tls_results = [
        {
            "domain": "z.example",
            "port": 443,
            "tls_version": "TLSv1.3",
            "cipher_suite": "TLS_AES_256_GCM_SHA384",
            "key_size": 4096,
        },
        {
            "domain": "a.example",
            "port": 443,
            "tls_version": "TLSv1.2",
            "cipher_suite": "TLS_AES_128_GCM_SHA256",
            "key_size": 2048,
        },
    ]

    pqc_scores, combined_reports = assess_tls_results(tls_results)

    assert [score["domain"] for score in pqc_scores] == [
        "z.example",
        "a.example",
    ]

    assert [report["domain"] for report in combined_reports] == [
        "z.example",
        "a.example",
    ]


def test_assessment_handles_tls_scan_errors():
    """A failed scan should still produce an assessment record."""

    tls_results = [
        {
            "domain": "unavailable.example",
            "port": 443,
            "error": "Simulated connection failure",
        }
    ]

    pqc_scores, combined_reports = assess_tls_results(tls_results)

    assert len(pqc_scores) == 1
    assert len(combined_reports) == 1

    assert combined_reports[0]["domain"] == "unavailable.example"
    assert combined_reports[0]["tls"]["error"] == ("Simulated connection failure")
    assert combined_reports[0]["pqc"] == pqc_scores[0]


def test_assess_tls_results_includes_pqc_exposure():
    tls_result = {
        "domain": "example.com",
        "port": 443,
        "tls_version": "TLSv1.3",
        "cipher_suite": "TLS_AES_256_GCM_SHA384",
        "cipher_strength": 256,
        "key_size": 2048,
        "public_key_algorithm": "RSA",
        "key_establishment_group": "X25519",
        "key_establishment_evidence_status": "observed",
        "key_establishment_source": "openssl_s_client_separate_handshake",
    }

    _, combined_reports = assess_tls_results([tls_result])

    assert len(combined_reports) == 1

    report = combined_reports[0]

    assert report["domain"] == "example.com"
    assert report["tls"] == tls_result
    assert "pqc" in report
    assert "pqc_exposure" in report

    key_establishment = report["pqc_exposure"]["key_establishment"]

    assert key_establishment["mechanism"] == "X25519"
    assert key_establishment["classification"] == "classical"
    assert key_establishment["evidence_status"] == "observed"
    assert key_establishment["rationale"]


def test_assess_tls_results_preserves_unknown_key_establishment():
    tls_result = {
        "domain": "example.org",
        "port": 443,
        "tls_version": "TLSv1.3",
        "cipher_suite": "TLS_AES_256_GCM_SHA384",
        "key_establishment_group": None,
        "key_establishment_evidence_status": "unavailable",
    }

    _, combined_reports = assess_tls_results([tls_result])

    key_establishment = combined_reports[0]["pqc_exposure"]["key_establishment"]

    assert key_establishment["classification"] == "unknown"
    assert key_establishment["evidence_status"] == "unavailable"
