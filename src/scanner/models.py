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

from typing import TypedDict


class TLSScanResult(TypedDict, total=False):
    """
    Structured representation of a single TLS scan result.

    All fields are optional (`total=False`) because servers may omit certain
    metadata (e.g., no certificate, no negotiated cipher, missing key size).

    Keys
    ----
    domain : str
        The scanned domain name.
    port : int
        The port used for the TLS handshake.
    tls_version : str | None
        Negotiated TLS version (e.g., "TLSv1.3").
    cipher_suite : str | None
        The negotiated cipher suite.
    cipher_strength : int | None
        Strength value reported by Python's SSL API.
    certificate_subject : dict[str, str]
        Parsed certificate subject fields.
    certificate_issuer : dict[str, str]
        Parsed certificate issuer fields.
    not_before : str | None
        Certificate validity start time.
    not_after : str | None
        Certificate validity end time.
    key_size : int | None
        Public key size extracted from the certificate.
    error : str
        Error message if the scan failed.
    scan_time_seconds : float
        Duration of the TLS scan in seconds.
    """

    domain: str
    port: int
    tls_version: str | None
    cipher_suite: str | None
    cipher_strength: int | None
    certificate_subject: dict[str, str]
    certificate_issuer: dict[str, str]
    not_before: str | None
    not_after: str | None
    key_size: int | None
    error: str
    scan_time_seconds: float


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


class CombinedTLSReport(TypedDict):
    """
    Unified TLS + PQC report object.

    This merges the raw TLS scan metadata with the PQC scoring output into a
    single structure suitable for reporting, exporting, dashboards, or further
    analysis.

    Keys
    ----
    domain : str
        The scanned domain name.
    tls : TLSScanResult
        Raw TLS metadata extracted from the handshake.
    pqc : PQCScore
        PQC scoring and risk classification.
    """

    domain: str
    tls: TLSScanResult
    pqc: PQCScore
