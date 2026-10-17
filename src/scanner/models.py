"""
Data Models for TLS Scanning and PQC Scoring

This module defines the structured data types used throughout the TLS scanner
pipeline. These TypedDict classes describe the shape of dictionaries returned
by the TLS scanning engine and the PQC scoring engine.

TypedDict is used because:
- It preserves normal dict behavior at runtime (no breaking changes).
- It provides strong static typing for mypy and IDEs.
- It documents the expected fields clearly.
"""

from typing import Literal, TypedDict


class _TLSSscanResultRequired(TypedDict):
    """
    Fileds that every TLS scan result must idntify.
    These fileds remain required even when the TLS scan fials.
    """

    domain: str
    port: int


class TLSScanResult(_TLSSscanResultRequired, total=False):
    """
    Structured representation of a single TLS scan result.

    The domain and port are always required. Other fields are
    optional because a scan may fail or return incomplete metadata.

    This TypedDict documents the expected structure for static
    type checking. It does not perform runtime validation.
    """

    # TLS connection information
    tls_version: str | None
    cipher_suite: str | None
    cipher_strength: int | None

    # Certificate identity and validity
    certificate_version: str | None
    certificate_serial_number: str | None
    certificate_subject: dict[str, str]
    certificate_issuer: dict[str, str]
    not_before: str | None
    not_after: str | None

    # Certificate public-key information
    public_key_algorithm: str | None
    key_size: int | None
    public_key_curve: str | None
    rsa_public_exponent: int | None

    # Certificate signature information
    certificate_signature_algorithm_oid: str | None
    certificate_signature_hash_algorithm: str | None

    # Certificate identity extensions
    san_dns_names: list[str]
    san_ip_addresses: list[str]

    # Certificate usage extensions
    key_usage: dict[str, bool] | None
    extended_key_usage: list[str] | None
    basic_constraints: dict[str, bool | int | None] | None

    # Key-establishment evidence
    key_establishment_group: str | None
    key_establishment_evidence_status: str
    key_establishment_source: str | None

    # Scan outcome and diagnostics
    error: str
    scan_time_seconds: float
    scan_status: Literal["success", "failed"]


class PQCScore(TypedDict):
    """
    Post-Quantum Cryptography (PQC) risk assessment for a scanned domain.

    This structure is always complete (`total=True` by default) because the
    scoring engine guarantees all fields are present.

    Keys
    ----
    domain : str
        The domain being evaluated.
    tls_score : int
        Composite TLS/PQC score between 0 and 100.
    pqc_risk : str
        Risk classification: "low", "medium", or "high".
    reasons : list[str]
        Human-readable explanations for the assigned score.
    """

    domain: str
    tls_score: int
    pqc_risk: str
    reasons: list[str]


class KeyEstablishmentAssessment(TypedDict):
    """Assessment of observed TLS key-establishment evidence."""

    mechanism: str | None
    classification: Literal["classical", "post_quantum", "hybrid", "unknown"]
    evidence_status: Literal["observed", "unavailable", "failed", "invalid"]
    source: str | None
    rationale: str


class PQCExposureAssessment(TypedDict):
    """
    Evidence-based assessment of post-quantum exposure.

    This assessment describes the observed key-establishment mechanism.
    It does not independently establish the endpoint's overall
    cryptographic security or PQC readiness.
    """

    key_establishment: KeyEstablishmentAssessment


class CombinedTLSReport(TypedDict):
    """
    Unified TLS and PQC assessment report.

    Combines the original TLS scan evidence, the existing heuristic
    score, and the separate evidence-based PQC exposure assessment.
    """

    domain: str
    tls: TLSScanResult
    pqc: PQCScore
    pqc_exposure: PQCExposureAssessment
