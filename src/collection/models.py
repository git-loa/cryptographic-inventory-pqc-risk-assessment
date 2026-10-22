"""
Data models for TLS collection evidence.

This module defines the typed structure used to represent the results
of TLS endpoint scans. The TLSScanResult model captures connection
metadata, certificate properties, key-establishment evidence, and
scan diagnostics.

The domain and port fields are required for every scan result,
including failed scans. Other fields are optional because a scan
may fail or produce incomplete evidence.

These models use TypedDict to support static type checking. They do
not perform runtime validation or guarantee that collected evidence
is accurate or complete.
"""

from typing import Literal, TypedDict


class _TLSScanResultRequired(TypedDict):
    """
    Define the fields required in every TLS scan result.

    Attributes:
        domain: Hostname or address of the TLS endpoint being scanned.
        port: Network port targeted by the TLS scan.
    """

    domain: str
    port: int


class TLSScanResult(_TLSScanResultRequired, total=False):
    """
    Represent the evidence collected during a TLS endpoint scan.

    This TypedDict provides a consistent structure for recording
    TLS connection details, certificate metadata, public-key
    characteristics, key-establishment evidence, and scan outcomes.

    The domain and port fields are always required. All other fields
    are optional because connection failures, unsupported features,
    or incomplete responses may prevent some evidence from being
    collected.

    Attributes:
        tls_version: Negotiated TLS protocol version.
        cipher_suite: Negotiated TLS cipher suite, when available.
        cipher_strength: Estimated cipher strength, when available.

        certificate_version: Version of the observed certificate.
        certificate_serial_number: Serial number of the certificate.
        certificate_subject: Subject distinguished-name attributes.
        certificate_issuer: Issuer distinguished-name attributes.
        not_before: Certificate validity start time.
        not_after: Certificate validity expiration time.

        public_key_algorithm: Algorithm used by the certificate's
            public key.
        key_size: Public-key size, when applicable and available.
        public_key_curve: Elliptic curve name, when applicable.
        rsa_public_exponent: RSA public exponent, when applicable.
        public_key_algorithm_oid: Object identifier for the public-key
            algorithm.

        certificate_signature_algorithm_oid: Object identifier for
            the certificate signature algorithm.
        certificate_signature_hash_algorithm: Hash algorithm used
            by the certificate signature, when identified.

        san_dns_names: DNS names listed in the Subject Alternative
            Name extension.
        san_ip_addresses: IP addresses listed in the Subject
            Alternative Name extension.

        key_usage: Certificate key-usage extension values.
        extended_key_usage: Certificate extended key-usage purposes.
        basic_constraints: Certificate authority and path-length
            constraint information.

        key_establishment_group: Observed key-establishment group,
            when available.
        key_establishment_evidence_status: Status describing the
            availability or reliability of key-establishment evidence.
        key_establishment_source: Source from which key-establishment
            evidence was obtained.

        error: Diagnostic message describing a scan failure, if any.
        scan_time_seconds: Duration of the scan in seconds.
        scan_status: Indicates whether the scan succeeded or failed.

    Note:
        TypedDict supports static type checking but does not validate
        values at runtime. Collection and validation logic must enforce
        any additional data-quality requirements.
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
