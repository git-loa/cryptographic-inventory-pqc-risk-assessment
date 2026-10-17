"""
PQC Scoring Engine

Takes TLSScanResult and produces a simple post-quantum risk score and labels.
"""

from src.scanner.models import TLSScanResult
from src.scanner.models import PQCScore


def classify_tls_version(
    tls_version: str | None,
) -> dict[str, str]:
    """Classify a negotiated TLS version using the A1 policy."""

    if tls_version == "TLSv1.3":
        classification = "acceptable"
        reason = "TLS 1.3 is the preferred modern TLS version."

    elif tls_version == "TLSv1.2":
        classification = "acceptable_with_review"
        reason = (
            "TLS 1.2 is supported, but other TLS configuration "
            "settings require review."
        )

    elif tls_version in {"TLSv1.0", "TLSv1.1", "SSLv2", "SSLv3"}:
        classification = "unacceptable"
        reason = "The negotiated protocol version is deprecated or insecure."

    else:
        classification = "unknown"
        reason = "The TLS version is missing or unrecognized."

    return {
        "dimension": "tls_version",
        "observed": tls_version or "unknown",
        "classification": classification,
        "reason": reason,
    }


def classify_cipher_suite(
    cipher_suite: str | None,
    tls_version: str | None,
    cipher_strength: int | None = None,
) -> dict[str, str]:
    """Classify a negotiated cipher suite using the A1 policy."""

    if not cipher_suite or not tls_version:
        classification = "unknown"
        reason = "Cipher-suite or TLS-version evidence is missing."

    else:
        suite = cipher_suite.upper()

        if "NULL" in suite or "RC4" in suite or "EXPORT" in suite:
            classification = "unacceptable"
            reason = (
                "The cipher suite uses NULL encryption, RC4, "
                "or export-grade cryptography."
            )

        elif cipher_strength is not None and cipher_strength < 112:
            classification = "unacceptable"
            reason = (
                "The reported cipher strength is below "
                "the 112-bit minimum in RFC 9325."
            )

        elif tls_version == "TLSv1.3":
            if suite in {
                "TLS_AES_128_GCM_SHA256",
                "TLS_AES_256_GCM_SHA384",
                "TLS_CHACHA20_POLY1305_SHA256",
            }:
                classification = "acceptable"
                reason = "The TLS 1.3 cipher suite uses a recognized AEAD construction."
            else:
                classification = "unknown"
                reason = (
                    "The TLS 1.3 cipher suite is not in "
                    "the currently recognized suite list."
                )

        elif tls_version == "TLSv1.2":
            if ("ECDHE-RSA-" in suite or "ECDHE_ECDSA_" in suite) and (
                "GCM" in suite or "CHACHA20-POLY1305" in suite
            ):
                classification = "acceptable"
                reason = (
                    "The recognized TLS 1.2 suite uses ephemeral "
                    "key agreement and authenticated encryption."
                )

            elif "CBC" in suite or "3DES" in suite:
                classification = "acceptable_with_review"
                reason = (
                    "The cipher suite uses CBC or 3DES and requires "
                    "additional review against RFC 9325."
                )

            else:
                classification = "unknown"
                reason = (
                    "The TLS 1.2 cipher suite is not covered "
                    "by the current classification rules."
                )

        else:
            classification = "unknown"
            reason = (
                "The TLS version is unrecognized; "
                "the cipher suite cannot be classified reliably."
            )

    return {
        "dimension": "cipher_suite",
        "observed": cipher_suite or "unknown",
        "classification": classification,
        "reason": reason,
    }


def classify_public_key_algorithm(
    public_key_algorithm: str | None,
) -> dict[str, str]:
    """Classify a certificate public-key algorithm under the A1.3 policy."""

    if not public_key_algorithm or not public_key_algorithm.strip():
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
        "observed": public_key_algorithm or "unknown",
        "classification": classification,
        "reason": reason,
    }


def classify_certificate_signature(
    signature_oid: str | None,
    hash_algorithm: str | None,
) -> dict[str, str]:
    """Classify a certificate signature under the initial A1.4 policy."""

    if not signature_oid:
        classification = "unknown"
        reason = "The certificate signature algorithm OID is unavailable."

    elif signature_oid in {
        "1.2.840.113549.1.1.5",  # sha1WithRSAEncryption
        "1.2.840.10045.4.1",  # ecdsa-with-SHA1
    }:
        classification = "unacceptable"
        reason = "The certificate uses a deprecated SHA-1 signature algorithm."

    elif signature_oid in {
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

    elif signature_oid == "1.2.840.113549.1.1.10":  # RSASSA-PSS
        normalized_hash = hash_algorithm.lower() if hash_algorithm else None

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

    elif signature_oid in {
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
            f"No classification rule exists for signature OID " f"{signature_oid!r}."
        )

    return {
        "dimension": "certificate_signature",
        "observed": signature_oid or "unknown",
        "classification": classification,
        "reason": reason,
    }


# -----------------------------------------------------------
# -------------------------------------------------------------


def _score_tls_version(tls_version: str | None) -> tuple[int, list[str]]:
    if tls_version is None:
        return 0, ["No TLS version negotiated"]

    if tls_version.startswith("TLSv1.3"):
        return 30, []
    if tls_version.startswith("TLSv1.2"):
        return 15, ["TLS 1.2 is weaker than TLS 1.3 for long-term PQC safety"]

    return 5, [f"Weak TLS version: {tls_version}"]


def _score_key_size(
    key_size: int | None,
    public_key_algorithm: str | None,
) -> tuple[int, list[str]]:
    """Score key size only when the public-key algorithm is recognized."""
    if key_size is None:
        return 0, ["Unknown key size"]

    if not public_key_algorithm:
        return 0, [
            "Public-key algorithm is unavailable;"
            "key size cannot be interpreted reliably."
        ]

    algorithm = public_key_algorithm.upper()

    # Apply these thresholds only to RSA keys.
    if algorithm == "RSA":
        if key_size >= 4096:
            return 30, []
        if key_size >= 2048:
            return 20, [
                "2048-bit RSA key: review classical security requirements "
                "and post-quantum migration needs"
            ]
        return 5, [f"Weak RSA key size: {key_size} bits"]

    # A key-size value alone is insufficient to assess EC key strength.
    if algorithm in {"EC", "ECDSA"}:
        return 0, [
            "EC key strength cannot be assessed from key size alone; "
            "curve information is needed"
        ]

    # Do not apply RSA thresholds to other or unrecognized algorithms.
    return 0, [
        f"No key-size scoring rule is defined for "
        f"public-key algorithm {public_key_algorithm!r}"
    ]


def _score_cipher_suite(cipher_suite: str | None) -> tuple[int, list[str]]:
    if cipher_suite is None:
        return 0, ["No cipher suite negotiated"]

    reasons: list[str] = []

    # Very rough heuristic: prefer AEAD + modern hashes
    score = 0
    if "AES_256" in cipher_suite or "CHACHA20" in cipher_suite:
        score += 15
    if "GCM" in cipher_suite or "POLY1305" in cipher_suite:
        score += 10
    if "SHA384" in cipher_suite or "SHA256" in cipher_suite:
        score += 5

    if "RSA" in cipher_suite:
        reasons.append("RSA key exchange is not PQC-safe (no KEM)")

    return score, reasons


def score_pqc(result: TLSScanResult) -> PQCScore:
    """
    Compute a simple PQC-oriented score from a TLSScanResult.
    """
    tls_version = result.get("tls_version")
    key_size = result.get("key_size")
    public_key_algorithm = result.get("public_key_algorithm")
    cipher_suite = result.get("cipher_suite")

    total_score = 0
    reasons: list[str] = []

    v_score, v_reasons = _score_tls_version(tls_version)
    total_score += v_score
    reasons.extend(v_reasons)

    k_score, k_reasons = _score_key_size(key_size, public_key_algorithm)
    total_score += k_score
    reasons.extend(k_reasons)

    c_score, c_reasons = _score_cipher_suite(cipher_suite)
    total_score += c_score
    reasons.extend(c_reasons)

    # Clamp to 0–100
    if total_score < 0:
        total_score = 0
    if total_score > 100:
        total_score = 100

    if total_score >= 70:
        pqc_risk = "low"
    elif total_score >= 40:
        pqc_risk = "medium"
    else:
        pqc_risk = "high"

    return {
        "domain": result["domain"],
        "tls_score": total_score,
        "pqc_risk": pqc_risk,
        "reasons": reasons,
    }
