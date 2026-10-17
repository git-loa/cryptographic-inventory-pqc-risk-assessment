"""
PQC Scoring Engine

Takes TLSScanResult and produces a simple post-quantum risk score and labels.
"""

from src.scanner.models import TLSScanResult
from src.scanner.models import PQCScore


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
