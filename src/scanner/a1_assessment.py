"""Structured A1 TLS configuration assessment."""

from src.scanner.models import A1Assessment, TLSScanResult
from src.scanner.pqc_scoring import (
    classify_certificate_signature,
    classify_cipher_suite,
    classify_public_key_algorithm,
    classify_tls_version,
)


def assess_a1_configuration(tls_result: TLSScanResult) -> A1Assessment:
    """Produce four evidence-linked A1 findings from one TLS scan result.

    Missing or unrecognized inputs remain `unknown`; this function does not
    infer a classification from unrelated fields or aggregate findings into
    a numerical score.
    """
    tls_version = tls_result.get("tls_version")
    return {
        "tls_version": classify_tls_version(tls_version),
        "cipher_suite": classify_cipher_suite(
            tls_result.get("cipher_suite"),
            tls_version,
        ),
        "public_key_algorithm": classify_public_key_algorithm(
            tls_result.get("public_key_algorithm"),
        ),
        "certificate_signature": classify_certificate_signature(
            tls_result.get("certificate_signature_algorithm_oid"),
            tls_result.get("certificate_signature_hash_algorithm"),
        ),
    }
