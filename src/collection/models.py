"""
Canonical data models for TLS collection evidence.

These models describe observations gathered from TLS endpoints.
They do not determine whether an endpoint is secure or PQC-ready.
"""

from typing import Literal, TypedDict

ScanStatus = Literal["success", "failed"]

KeyEstablishmentEvidenceStatus = Literal[
    "observed",
    "unavailable",
    "not_attempted",
]


class _TLSScanResultRequired(TypedDict):
    """Fields required in every TLS scan result."""

    domain: str
    port: int
    scan_status: ScanStatus
    scan_time_seconds: float
    key_establishment_evidence_status: KeyEstablishmentEvidenceStatus


class TLSScanResult(_TLSScanResultRequired, total=False):
    """Evidence collected from one TLS endpoint."""

    # Negotiated TLS connection
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

    # Certificate public key
    public_key_algorithm: str | None
    public_key_variant: str | None
    public_key_algorithm_oid: str | None
    key_size: int | None
    public_key_curve: str | None
    rsa_public_exponent: int | None

    # Certificate signature
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
    key_establishment_source: str | None

    # Diagnostics
    error: str
