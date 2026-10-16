import pytest

from src.scanner.pqc_assessment import assess_pqc_exposure


def make_tls_result(**overrides):
    """Create a minimal TLS result for PQC assessment tests."""
    result = {
        "domain": "example.com",
        "tls_version": None,
        "cipher_suite": None,
        "key_establishment_group": None,
        "key_establishment_evidence_status": "unavailable",
        "key_establishment_source": None,
        "public_key_algorithm": None,
        "certificate_signature_algorithm": None,
        "error": None,
    }

    result.update(overrides)
    return result


def test_tls_13_does_not_imply_pqc_readiness():
    result = make_tls_result(tls_version="TLSv1.3")

    assessment = assess_pqc_exposure(result)

    assert assessment["key_establishment"]["classification"] == "unknown"


def test_aes_256_does_not_imply_pqc_readiness():
    result = make_tls_result(
        tls_version="TLSv1.3",
        cipher_suite="TLS_AES_256_GCM_SHA384",
    )

    assessment = assess_pqc_exposure(result)

    assert assessment["key_establishment"]["classification"] == "unknown"


@pytest.mark.parametrize("group", ["X25519", "secp256r1"])
def test_observed_classical_group_is_classified_as_classical(group):
    result = make_tls_result(
        key_establishment_group=group,
        key_establishment_evidence_status="observed",
        key_establishment_source="openssl_s_client",
    )

    assessment = assess_pqc_exposure(result)
    key_establishment = assessment["key_establishment"]

    assert key_establishment["mechanism"] == group
    assert key_establishment["classification"] == "classical"
    assert key_establishment["evidence_status"] == "observed"


def test_rsa_certificate_key_does_not_determine_key_establishment():
    result = make_tls_result(
        public_key_algorithm="RSA",
        key_establishment_evidence_status="unavailable",
    )

    assessment = assess_pqc_exposure(result)

    assert assessment["key_establishment"]["classification"] == "unknown"


def test_missing_evidence_is_not_confirmed_quantum_exposure():
    result = make_tls_result(
        key_establishment_group=None,
        key_establishment_evidence_status="unavailable",
    )

    assessment = assess_pqc_exposure(result)
    key_establishment = assessment["key_establishment"]

    assert key_establishment["classification"] == "unknown"
    assert key_establishment["evidence_status"] == "unavailable"


def test_failed_tls_scan_does_not_imply_successful_negotiation():
    result = make_tls_result(
        error="TLS handshake failed",
    )

    assessment = assess_pqc_exposure(result)
    key_establishment = assessment["key_establishment"]

    assert key_establishment["classification"] == "unknown"
    assert key_establishment["evidence_status"] == "failed"


def test_key_establishment_is_assessed_independently_of_cipher_suite():
    result = make_tls_result(
        tls_version="TLSv1.3",
        cipher_suite="TLS_AES_256_GCM_SHA384",
        key_establishment_group="X25519",
        key_establishment_evidence_status="observed",
        key_establishment_source="openssl_s_client",
    )

    assessment = assess_pqc_exposure(result)

    assert assessment["key_establishment"]["classification"] == "classical"


def test_unrecognized_group_is_not_assumed_to_be_classical():
    result = make_tls_result(
        key_establishment_group="UNRECOGNIZED_GROUP",
        key_establishment_evidence_status="observed",
        key_establishment_source="openssl_s_client",
    )

    assessment = assess_pqc_exposure(result)

    assert assessment["key_establishment"]["classification"] == "unknown"


def test_assessment_includes_explanation():
    result = make_tls_result(
        key_establishment_group="X25519",
        key_establishment_evidence_status="observed",
        key_establishment_source="openssl_s_client",
    )

    assessment = assess_pqc_exposure(result)
    key_establishment = assessment["key_establishment"]

    assert key_establishment["rationale"]


def test_group_is_not_trusted_when_evidence_status_is_unavailable():
    result = make_tls_result(
        key_establishment_group="X25519",
        key_establishment_evidence_status="unavailable",
    )

    assessment = assess_pqc_exposure(result)
    key_establishment = assessment["key_establishment"]

    assert key_establishment["classification"] == "unknown"
    assert key_establishment["evidence_status"] == "unavailable"
    assert key_establishment["mechanism"] is None
    assert "identifier was supplied" in key_establishment["rationale"]


def test_unrecognized_evidence_status_is_marked_invalid():
    result = make_tls_result(
        key_establishment_group="X25519",
        key_establishment_evidence_status="confirmed",
    )

    assessment = assess_pqc_exposure(result)
    key_establishment = assessment["key_establishment"]

    assert key_establishment["classification"] == "unknown"
    assert key_establishment["evidence_status"] == "invalid"
    assert key_establishment["mechanism"] is None


def test_empty_group_with_observed_status_remains_unknown():
    result = make_tls_result(
        key_establishment_group="",
        key_establishment_evidence_status="observed",
    )

    assessment = assess_pqc_exposure(result)
    key_establishment = assessment["key_establishment"]

    assert key_establishment["classification"] == "unknown"
    assert key_establishment["evidence_status"] == "observed"
    assert key_establishment["mechanism"] == ""
    assert key_establishment["rationale"]


def test_assessment_preserves_key_establishment_source():
    result = make_tls_result(
        key_establishment_group="X25519",
        key_establishment_evidence_status="observed",
        key_establishment_source="openssl_s_client_separate_handshake",
    )

    assessment = assess_pqc_exposure(result)
    key_establishment = assessment["key_establishment"]

    assert key_establishment["source"] == "openssl_s_client_separate_handshake"


def test_unavailable_evidence_does_not_claim_an_observed_mechanism():
    result = make_tls_result(
        key_establishment_group=None,
        key_establishment_evidence_status="unavailable",
        key_establishment_source="openssl_s_client_separate_handshake",
    )

    assessment = assess_pqc_exposure(result)
    key_establishment = assessment["key_establishment"]

    assert key_establishment["mechanism"] is None
    assert key_establishment["classification"] == "unknown"
    assert key_establishment["evidence_status"] == "unavailable"
    assert key_establishment["source"] == "openssl_s_client_separate_handshake"


def test_failed_primary_scan_overrides_observed_group():
    result = make_tls_result(
        error="TLS handshake failed",
        key_establishment_group="X25519",
        key_establishment_evidence_status="observed",
        key_establishment_source="openssl_s_client_separate_handshake",
    )

    assessment = assess_pqc_exposure(result)
    key_establishment = assessment["key_establishment"]

    assert key_establishment["mechanism"] is None
    assert key_establishment["classification"] == "unknown"
    assert key_establishment["evidence_status"] == "failed"
    assert key_establishment["source"] == "openssl_s_client_separate_handshake"
    assert "successful" in key_establishment["rationale"]


def test_failed_scan_status_overrides_observed_group():
    """A failed primary scan must override contradictory group evidence."""
    result = make_tls_result(
        scan_status="failed",
        key_establishment_group="X25519",
        key_establishment_evidence_status="observed",
        key_establishment_source="openssl_s_client_separate_handshake",
    )

    assessment = assess_pqc_exposure(result)
    key_establishment = assessment["key_establishment"]

    assert key_establishment["mechanism"] is None
    assert key_establishment["classification"] == "unknown"
    assert key_establishment["evidence_status"] == "failed"
    assert "successful" in key_establishment["rationale"]


def test_unrecognized_scan_status_does_not_trust_observed_group():
    """An invalid scan status must not establish a reliable negotiation."""
    result = make_tls_result(
        scan_status="unexpected",
        key_establishment_group="X25519",
        key_establishment_evidence_status="observed",
        key_establishment_source="openssl_s_client_separate_handshake",
    )

    assessment = assess_pqc_exposure(result)
    key_establishment = assessment["key_establishment"]

    assert key_establishment["mechanism"] is None
    assert key_establishment["classification"] == "unknown"
    assert key_establishment["evidence_status"] == "invalid"


def test_success_status_with_error_does_not_trust_observed_group():
    """A contradictory scan error must prevent trusting group evidence."""
    result = make_tls_result(
        scan_status="success",
        error="TLS handshake failed",
        key_establishment_group="X25519",
        key_establishment_evidence_status="observed",
        key_establishment_source="openssl_s_client_separate_handshake",
    )

    assessment = assess_pqc_exposure(result)
    key_establishment = assessment["key_establishment"]

    assert key_establishment["mechanism"] is None
    assert key_establishment["classification"] == "unknown"
    assert key_establishment["evidence_status"] == "invalid"
