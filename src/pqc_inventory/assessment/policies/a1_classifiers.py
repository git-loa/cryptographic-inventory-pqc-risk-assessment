"A1 Classifiers"


def classify_tls_version(
    tls_version: str | None,
) -> dict[str, str]:
    """Classify a negotiated TLS version using the A1.1 policy.

    Comparison is case-insensitive and ignores surrounding whitespace.
    Missing, empty, non-string, or unrecognized evidence remains unknown.
    """
    normalized = tls_version.strip().upper() if isinstance(tls_version, str) else ""

    if tls_version is None:
        classification = "unknown"
        reason = "TLS-version evidence is missing."

    elif not isinstance(tls_version, str):
        classification = "unknown"
        reason = "TLS-version evidence has an invalid type."

    elif not tls_version.strip():
        classification = "unknown"
        reason = "TLS-version evidence is empty."

    elif normalized == "TLSV1.3":
        classification = "acceptable"
        reason = "TLS 1.3 is the preferred modern TLS version."

    elif normalized == "TLSV1.2":
        classification = "acceptable_with_review"
        reason = (
            "TLS 1.2 is supported, but other TLS configuration "
            "settings require review."
        )

    elif normalized in {"TLSV1.0", "TLSV1.1", "SSLV2", "SSLV3"}:
        classification = "unacceptable"
        reason = "The negotiated protocol version is deprecated or insecure."

    else:
        classification = "unknown"
        reason = "The TLS version is unrecognized."

    return {
        "dimension": "tls_version",
        "observed": (
            tls_version.strip()
            if isinstance(tls_version, str) and tls_version.strip()
            else "unknown"
        ),
        "classification": classification,
        "reason": reason,
    }


def _cipher_suite_result(
    cipher_suite: str | None,
    classification: str,
    reason: str,
) -> dict[str, str]:
    """Build a consistent cipher-suite assessment result."""

    return {
        "dimension": "cipher_suite",
        "observed": (
            cipher_suite.strip()
            if isinstance(cipher_suite, str) and cipher_suite.strip()
            else "unknown"
        ),
        "classification": classification,
        "reason": reason,
    }


def _is_unacceptable_cipher_suite(cipher_suite: str) -> bool:
    """Identify cipher suites excluded from the project baseline."""

    return (
        any(marker in cipher_suite for marker in ("NULL", "RC4", "EXPORT"))
        or "3DES" in cipher_suite
        or "DES-CBC3" in cipher_suite
    )


def _classify_tls13_cipher_suite(
    cipher_suite: str,
) -> tuple[str, str]:
    """Apply the initial TLS 1.3 cipher-suite policy."""

    acceptable_suites = {
        "TLS_AES_128_GCM_SHA256",
        "TLS_AES_256_GCM_SHA384",
        "TLS_CHACHA20_POLY1305_SHA256",
        "TLS_AES_128_CCM_SHA256",
    }

    if cipher_suite == "TLS_AES_128_CCM_8_SHA256":
        return (
            "acceptable_with_review",
            "The TLS 1.3 CCM_8 suite uses a truncated authentication "
            "tag and requires additional security review.",
        )

    if cipher_suite in acceptable_suites:
        return (
            "acceptable",
            "The TLS 1.3 cipher suite is in the project's recognized "
            "AEAD allowlist.",
        )

    return (
        "unknown",
        "The TLS 1.3 cipher suite is not covered by the current "
        "classification rules.",
    )


def _classify_tls12_cipher_suite(
    cipher_suite: str,
) -> tuple[str, str]:
    """Apply the initial TLS 1.2 cipher-suite policy."""

    ecdhe_aead_suites = {
        "ECDHE-RSA-AES128-GCM-SHA256",
        "ECDHE-RSA-AES256-GCM-SHA384",
        "ECDHE-ECDSA-AES128-GCM-SHA256",
        "ECDHE-ECDSA-AES256-GCM-SHA384",
        "ECDHE-RSA-CHACHA20-POLY1305",
        "ECDHE-ECDSA-CHACHA20-POLY1305",
        "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
        "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
        "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
        "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
        "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256",
        "TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256",
    }

    static_rsa_suites = {
        "AES128-GCM-SHA256",
        "AES256-GCM-SHA384",
        "AES128-SHA",
        "AES256-SHA",
        "AES128-SHA256",
        "AES256-SHA256",
        "AES256-SHA384",
        "TLS_RSA_WITH_AES_128_GCM_SHA256",
        "TLS_RSA_WITH_AES_256_GCM_SHA384",
        "TLS_RSA_WITH_AES_128_CBC_SHA",
        "TLS_RSA_WITH_AES_256_CBC_SHA",
        "TLS_RSA_WITH_AES_128_CBC_SHA256",
        "TLS_RSA_WITH_AES_256_CBC_SHA256",
    }

    ecdhe_cbc_suites = {
        "ECDHE-RSA-AES128-SHA",
        "ECDHE-RSA-AES256-SHA",
        "ECDHE-ECDSA-AES128-SHA",
        "ECDHE-ECDSA-AES256-SHA",
        "ECDHE-RSA-AES128-SHA256",
        "ECDHE-RSA-AES256-SHA384",
        "ECDHE-ECDSA-AES128-SHA256",
        "ECDHE-ECDSA-AES256-SHA384",
        "ECDHE-RSA-AES128-CBC-SHA",
        "ECDHE-RSA-AES256-CBC-SHA",
        "ECDHE-ECDSA-AES128-CBC-SHA",
        "ECDHE-ECDSA-AES256-CBC-SHA",
        "ECDHE-RSA-AES128-CBC-SHA256",
        "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA",
        "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
        "TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA",
        "TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA",
        "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256",
        "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA384",
        "TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA256",
        "TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA384",
    }

    if cipher_suite in ecdhe_aead_suites:
        return (
            "acceptable",
            "The recognized TLS 1.2 suite uses ephemeral key agreement "
            "and authenticated encryption.",
        )

    if cipher_suite in static_rsa_suites:
        return (
            "acceptable_with_review",
            "The recognized TLS 1.2 suite uses static RSA key transport "
            "and lacks forward secrecy.",
        )

    if cipher_suite in ecdhe_cbc_suites:
        return (
            "acceptable_with_review",
            "The recognized TLS 1.2 suite uses CBC mode and requires "
            "additional review against the project's TLS policy.",
        )

    return (
        "unknown",
        "The TLS 1.2 cipher suite is not covered by the current "
        "classification rules.",
    )


def classify_cipher_suite(
    cipher_suite: str | None,
    tls_version: str | None,
) -> dict[str, str]:
    """Classify a negotiated cipher suite using the A1.2 policy."""

    if not isinstance(cipher_suite, str) or not cipher_suite.strip():
        return _cipher_suite_result(
            cipher_suite,
            "unknown",
            "Cipher-suite evidence is missing.",
        )

    suite = cipher_suite.strip().upper()

    if _is_unacceptable_cipher_suite(suite):
        return _cipher_suite_result(
            cipher_suite,
            "unacceptable",
            "The observed cipher-suite name matches an explicitly "
            "excluded pattern: NULL, RC4, EXPORT, or 3DES.",
        )

    if not isinstance(tls_version, str) or not tls_version.strip():
        return _cipher_suite_result(
            cipher_suite,
            "unknown",
            "TLS-version evidence is missing or invalid.",
        )

    version = tls_version.strip().upper()

    if version == "TLSV1.3":
        classification, reason = _classify_tls13_cipher_suite(suite)

    elif version == "TLSV1.2":
        classification, reason = _classify_tls12_cipher_suite(suite)

    else:
        classification = "unknown"
        reason = (
            "The TLS version is unrecognized; the cipher suite "
            "cannot be classified reliably."
        )

    return _cipher_suite_result(cipher_suite, classification, reason)


def classify_public_key_algorithm(
    public_key_algorithm: str | None,
) -> dict[str, str]:
    """Classify a certificate public-key algorithm under the A1.3 policy."""

    if not isinstance(public_key_algorithm, str) or not public_key_algorithm.strip():
        classification = "unknown"
        reason = "The certificate public-key algorithm is unavailable."

    else:
        algorithm = public_key_algorithm.strip().upper()

        if algorithm == "ML-DSA":
            classification = "acceptable"
            reason = (
                "ML-DSA is a standardized post-quantum " "digital-signature algorithm."
            )

        elif algorithm in {"RSA", "EC", "ED25519", "ED448"}:
            classification = "acceptable_with_review"
            reason = (
                f"{public_key_algorithm} is a classical public-key "
                "algorithm requiring post-quantum migration review."
            )

        elif algorithm == "DSA":
            classification = "unacceptable"
            reason = (
                "DSA is excluded from the project's initial "
                "acceptable algorithm baseline."
            )

        else:
            classification = "unknown"
            reason = (
                f"No classification rule exists for public-key "
                f"algorithm {public_key_algorithm!r}."
            )

    return {
        "dimension": "public_key_algorithm",
        "observed": (
            public_key_algorithm.strip()
            if isinstance(public_key_algorithm, str) and public_key_algorithm.strip()
            else "unknown"
        ),
        "classification": classification,
        "reason": reason,
    }


def classify_certificate_signature(
    signature_oid: str | None,
    hash_algorithm: str | None,
) -> dict[str, str]:
    """Classify a certificate signature under the initial A1.4 policy."""

    normalized_oid = signature_oid.strip() if isinstance(signature_oid, str) else ""

    if not normalized_oid:
        classification = "unknown"
        reason = "The certificate signature algorithm OID is unavailable."

    elif normalized_oid in {
        "1.2.840.113549.1.1.5",  # sha1WithRSAEncryption
        "1.2.840.10045.4.1",  # ecdsa-with-SHA1
    }:
        classification = "unacceptable"
        reason = "The certificate uses a deprecated SHA-1 signature algorithm."

    elif normalized_oid in {
        "1.2.840.113549.1.1.11",  # sha256WithRSAEncryption
        "1.2.840.113549.1.1.12",  # sha384WithRSAEncryption
        "1.2.840.113549.1.1.13",  # sha512WithRSAEncryption
        "1.2.840.10045.4.3.2",  # ecdsa-with-SHA256
        "1.2.840.10045.4.3.3",  # ecdsa-with-SHA384
        "1.2.840.10045.4.3.4",  # ecdsa-with-SHA512
        "1.3.101.112",  # Ed25519
        "1.3.101.113",  # Ed448
    }:
        classification = "acceptable_with_review"
        reason = (
            "The certificate uses a recognized classical signature "
            "algorithm requiring post-quantum migration review."
        )

    elif normalized_oid == "1.2.840.113549.1.1.10":  # RSASSA-PSS
        normalized_hash = (
            hash_algorithm.strip().lower()
            if isinstance(hash_algorithm, str) and hash_algorithm.strip()
            else None
        )

        if normalized_hash in {"sha256", "sha384", "sha512"}:
            classification = "acceptable_with_review"
            reason = (
                "RSA-PSS uses a recognized hash algorithm but remains "
                "a classical signature scheme requiring PQC migration review."
            )
        else:
            classification = "unknown"
            reason = (
                "RSA-PSS parameters or hash evidence are insufficient "
                "for classification."
            )

    elif normalized_oid in {
        "2.16.840.1.101.3.4.3.17",  # ML-DSA-44
        "2.16.840.1.101.3.4.3.18",  # ML-DSA-65
        "2.16.840.1.101.3.4.3.19",  # ML-DSA-87
    }:
        classification = "acceptable"
        reason = (
            "The certificate uses a recognized standardized "
            "post-quantum signature algorithm."
        )

    else:
        classification = "unknown"
        reason = (
            f"No classification rule exists for signature OID " f"{normalized_oid!r}."
        )

    return {
        "dimension": "certificate_signature",
        "observed": normalized_oid or "unknown",
        "classification": classification,
        "reason": reason,
    }
