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
    scan_status = tls_result.get("scan_status")
    group = tls_result.get("key_establishment_group")
    evidence_status = tls_result.get("key_establishment_evidence_status")
    source = tls_result.get("key_establishment_source")
    error = tls_result.get("error")

    # A failed primary TLS scan cannot establish a successful negotiation.
    # Preserve compatibility with older results that lack scan_status.
    if scan_status == "failed" or (scan_status is None and error):
        return {
            "key_establishment": {
                "mechanism": None,
                "classification": "unknown",
                "evidence_status": "failed",
                "source": source,
                "rationale": (
                    "The TLS scan reported a failure. A successful "
                    "key-establishment negotiation has not been established."
                ),
            }
        }

    # Accept only evidence statuses defined by the scanner.
    valid_evidence_statuses = {"observed", "unavailable"}

    if evidence_status not in valid_evidence_statuses:
        return {
            "key_establishment": {
                "mechanism": None,
                "classification": "unknown",
                "evidence_status": "invalid",
                "source": source,
                "rationale": (
                    "The key-establishment evidence status is missing or "
                    "unrecognized. The mechanism cannot be classified reliably."
                ),
            }
        }

    # A group identifier is not trustworthy unless its evidence
    # status explicitly confirms that it was observed.
    if evidence_status == "unavailable":
        rationale = (
            "Key-establishment evidence is unavailable. "
            if not group
            else (
                "A key-establishment identifier was supplied, but its evidence "
                "status is unavailable. The identifier cannot be trusted "
                "as an observed negotiation."
            )
        )

        return {
            "key_establishment": {
                "mechanism": None,
                "classification": "unknown",
                "evidence_status": "unavailable",
                "source": source,
                "rationale": rationale,
            }
        }

    # We observed an identifier, but that does not mean we recognize it.
    if not group or not isinstance(group, str):
        return {
            "key_establishment": {
                "mechanism": group,
                "classification": "unknown",
                "evidence_status": "observed",
                "source": source,
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
            "source": source,
            "rationale": rationale,
        }
    }
