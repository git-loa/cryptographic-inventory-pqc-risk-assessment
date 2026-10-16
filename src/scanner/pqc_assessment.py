"""Assess post-quantum exposure using observed TLS key-establishment evidence."""

from typing import Any

# Explicitly recognized classical key-establishment groups.
# Unknown identifiers must not automatically be classified as classical or PQC.
CLASSICAL_GROUPS = {
    "X25519",
    "secp256r1",
}


def assess_pqc_exposure(tls_result: dict[str, Any]) -> dict[str, Any]:
    """
    Assess PQC exposure from the available TLS scan evidence.

    This assessment classifies observed key-establishment mechanisms.
    It does not infer PQC readiness from the TLS version, cipher suite,
    or certificate public-key algorithm.
    """
    group = tls_result.get("key_establishment_group")
    evidence_status = tls_result.get("key_establishment_evidence_status")
    error = tls_result.get("error")

    # A failed primary TLS scan cannot establish a successful negotiation.
    if error:
        return {
            "key_establishment": {
                "mechanism": None,
                "classification": "unknown",
                "evidence_status": "failed",
                "rationale": (
                    "The TLS scan reported an error. A successful "
                    "key-establishment negotiation has not been established."
                ),
            }
        }

    # Do not treat a group identifier as reliable evidence unless
    # the scanner explicitly records the evidence as observed.
    if evidence_status != "observed":
        return {
            "key_establishment": {
                "mechanism": None,
                "classification": "unknown",
                "evidence_status": evidence_status or "unavailable",
                "rationale": (
                    "Key-establishment evidence was not confirmed as observed. "
                    "The mechanism cannot be classified from the available evidence."
                ),
            }
        }

    # We observed an identifier, but that does not mean we recognize it.
    if not group or not isinstance(group, str):
        return {
            "key_establishment": {
                "mechanism": group,
                "classification": "unknown",
                "evidence_status": "observed",
                "rationale": (
                    "The evidence is marked as observed, but no usable "
                    "key-establishment group identifier is available."
                ),
            }
        }

    # Classify only identifiers explicitly included in our registry.
    if group in CLASSICAL_GROUPS:
        classification = "classical"
        rationale = (
            f"The observed key-establishment group {group} is a recognized "
            "classical mechanism and is not post-quantum key establishment."
        )
    else:
        classification = "unknown"
        rationale = (
            f"The observed identifier {group} is not in the current verified "
            "mechanism registry. Its classification remains unknown."
        )

    return {
        "key_establishment": {
            "mechanism": group,
            "classification": classification,
            "evidence_status": "observed",
            "rationale": rationale,
        }
    }
