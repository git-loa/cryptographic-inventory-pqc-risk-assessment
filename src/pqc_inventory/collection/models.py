"""
Canonical data contracts for TLS collection evidence.

These models describe observations collected from TLS endpoints.
They do not determine whether an endpoint is secure or PQC-ready.
"""

from typing import Literal, TypedDict

# Increment when the externally consumed scan-result schema changes.
SCAN_SCHEMA_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Target contracts
# ---------------------------------------------------------------------------

TargetType = Literal[
    "domain",
    "ipv4",
    "ipv6",
]


# ---------------------------------------------------------------------------
# Scan status contracts
# ---------------------------------------------------------------------------

ScanStatus = Literal[
    "completed",
    "partial",
    "failed",
]

KeyEstablishmentEvidenceStatus = Literal[
    "observed",
    "unavailable",
    "not_attempted",
]

CertificateVerificationStatus = Literal[
    "verified",
    "failed",
    "not_performed",
    "unknown",
]


# ---------------------------------------------------------------------------
# Diagnostic contracts
# ---------------------------------------------------------------------------

DiagnosticSeverity = Literal[
    "info",
    "warning",
    "error",
]

DiagnosticCategory = Literal[
    "input_validation",
    "connection",
    "timeout",
    "certificate",
    "key_establishment",
    "parsing",
    "internal",
]


class ScanDiagnostic(TypedDict):
    """A structured diagnostic produced during collection."""

    code: str
    category: DiagnosticCategory
    severity: DiagnosticSeverity
    message: str
    stage: str


# ---------------------------------------------------------------------------
# Required scan-result fields
# ---------------------------------------------------------------------------


class _TLSScanResultRequired(TypedDict):
    """Fields required in every canonical scan result."""

    schema_version: str
    scan_id: str

    # Original target supplied for scanning.
    target: str
    target_type: TargetType

    # TCP port used for the TLS connection.
    port: int

    # IP address actually contacted, or None if it could not be determined.
    resolved_ip_address: str | None

    scan_status: ScanStatus

    started_at: str
    completed_at: str | None
    scan_time_seconds: float

    certificate_verification_status: CertificateVerificationStatus
    certificate_verification_error: str | None

    key_establishment_evidence_status: KeyEstablishmentEvidenceStatus

    diagnostics: list[ScanDiagnostic]


# ---------------------------------------------------------------------------
# Canonical TLS scan result
# ---------------------------------------------------------------------------


class TLSScanResult(_TLSScanResultRequired, total=False):
    """
    Normalized TLS collection result.

    Required fields describe target identity, lifecycle, status, verification,
    and diagnostics. Optional fields contain evidence that may not be
    available for every endpoint or collection attempt.
    """

    # -----------------------------------------------------------------------
    # Negotiated TLS connection
    # -----------------------------------------------------------------------

    tls_version: str | None
    cipher_suite: str | None
    cipher_strength: int | None

    # -----------------------------------------------------------------------
    # Certificate metadata
    # -----------------------------------------------------------------------

    certificate_version: str | None
    certificate_serial_number: str | None

    certificate_subject: dict[str, str]
    certificate_issuer: dict[str, str]

    not_before: str | None
    not_after: str | None

    # -----------------------------------------------------------------------
    # Certificate public key
    # -----------------------------------------------------------------------

    public_key_algorithm: str | None
    public_key_variant: str | None
    public_key_algorithm_oid: str | None

    key_size: int | None
    public_key_curve: str | None
    rsa_public_exponent: int | None

    # -----------------------------------------------------------------------
    # Certificate signature
    # -----------------------------------------------------------------------

    certificate_signature_algorithm_oid: str | None
    certificate_signature_hash_algorithm: str | None

    # -----------------------------------------------------------------------
    # Certificate identity extensions
    # -----------------------------------------------------------------------

    san_dns_names: list[str]
    san_ip_addresses: list[str]

    # -----------------------------------------------------------------------
    # Certificate usage extensions
    # -----------------------------------------------------------------------

    key_usage: dict[str, bool] | None
    extended_key_usage: list[str] | None
    basic_constraints: dict[str, bool | int | None] | None

    # -----------------------------------------------------------------------
    # Key-establishment evidence
    # -----------------------------------------------------------------------

    key_establishment_group: str | None

    # Identifies the source of the evidence.
    # Examples: "python_ssl", "openssl_cli_separate_handshake".
    key_establishment_source: str | None
