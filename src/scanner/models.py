"""
Data models for TLS scanning and cryptographic assessment.

TypedDict defines the expected structures used by the scanner,
A1 assessment engine, and reporting pipeline.
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
    public_key_algorithm_oid: str | None

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


class A1Finding(TypedDict):
    """One evidence-linked TLS configuration classification."""

    dimension: str
    observed: str
    classification: Literal[
        "acceptable",
        "acceptable_with_review",
        "unacceptable",
        "unknown",
    ]
    reason: str


class A1Assessment(TypedDict):
    """Structured A1 findings; no composite score is implied."""

    tls_version: A1Finding
    cipher_suite: A1Finding
    public_key_algorithm: A1Finding
    certificate_signature: A1Finding


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

    Combines original TLS scan evidence, structured A1 findings, the legacy
    heuristic score, and the separate evidence-based PQC exposure assessment.
    """

    domain: str
    tls: TLSScanResult
    a1: A1Assessment
