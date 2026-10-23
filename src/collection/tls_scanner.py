"""Collect TLS connection and certificate evidence from an endpoint.

This module collects observations only. It does not determine whether an
endpoint is secure or post-quantum cryptography (PQC) ready.
"""

from __future__ import annotations

import math
import socket
import ssl
import time

from cryptography.exceptions import UnsupportedAlgorithm

from src.collection.certificate_parser import parse_certificate
from src.collection.key_establishment import collect_key_establishment_group
from src.collection.models import TLSScanResult
from src.utils.logger import get_logger

logger = get_logger(__name__)


def validate_domain_or_error(
    domain: str,
    port: int = 443,
) -> TLSScanResult | None:
    """Validate endpoint input before any network activity."""

    if not isinstance(domain, str) or not domain:
        return _error_result(
            domain if isinstance(domain, str) else "",
            port if isinstance(port, int) and not isinstance(port, bool) else 443,
            "Invalid domain name",
            0.0,
        )

    if not isinstance(port, int) or isinstance(port, bool):
        return _error_result(
            domain,
            443,
            "Invalid port",
            0.0,
        )

    if not 1 <= port <= 65535:
        return _error_result(
            domain,
            443,
            "Invalid port",
            0.0,
        )
    # A trailing dot is permitted for a fully qualified DNS name.
    hostname = domain[:-1] if domain.endswith(".") else domain

    if not hostname or len(hostname) > 253:
        return _error_result(domain, port, "Invalid domain name", 0.0)

    # Normalize internationalized domain names for validation. The original
    # input remains the endpoint identifier used in the scan result.
    try:
        ascii_hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError:
        return _error_result(domain, port, "Invalid domain name", 0.0)

    labels = ascii_hostname.split(".")

    # Require at least two labels, such as example.com
    if len(labels) < 2:
        return _error_result(
            domain,
            port,
            "Invalid domain name",
            0.0,
        )

    for label in labels:
        if not label or len(label) > 63:
            return _error_result(domain, port, "Invalid domain name", 0.0)

        if label.startswith("-") or label.endswith("-"):
            return _error_result(domain, port, "Invalid domain name", 0.0)

        if not all(character.isalnum() or character == "-" for character in label):
            return _error_result(domain, port, "Invalid domain name", 0.0)

    return None


def _error_result(
    domain: str,
    port: int,
    message: str,
    elapsed: float,
) -> TLSScanResult:
    """Build a consistent failed result without inventing observations."""

    return {
        "domain": domain,
        "port": port,
        "scan_status": "failed",
        "tls_version": None,
        "cipher_suite": None,
        "cipher_strength": None,
        "certificate_subject": {},
        "certificate_issuer": {},
        "not_before": None,
        "not_after": None,
        "key_size": None,
        "error": message,
        "scan_time_seconds": max(0.0, elapsed),
        "public_key_algorithm": None,
        "public_key_variant": None,
        "public_key_algorithm_oid": None,
        "key_establishment_group": None,
        "key_establishment_evidence_status": "not_attempted",
        "key_establishment_source": None,
        "certificate_version": None,
        "certificate_serial_number": None,
        "public_key_curve": None,
        "rsa_public_exponent": None,
        "certificate_signature_algorithm_oid": None,
        "certificate_signature_hash_algorithm": None,
        "san_dns_names": [],
        "san_ip_addresses": [],
        "key_usage": None,
        "extended_key_usage": None,
        "basic_constraints": None,
    }


def _handle_connection_error(
    error: Exception,
    domain: str,
    port: int,
    start: float,
) -> TLSScanResult:
    """Translate expected connection failures into collection results."""

    elapsed = time.perf_counter() - start

    if isinstance(error, ssl.SSLError):
        message = f"SSL error: {error}"
    elif isinstance(error, socket.timeout):
        message = f"Timeout: {error}"
    elif isinstance(error, socket.gaierror):
        message = f"DNS error: {error}"
    else:
        message = f"Connection error: {error}"

    return _error_result(domain, port, message, elapsed)


def _scan_tls_connection(
    domain: str,
    port: int,
    timeout: float,
    start: float,
) -> TLSScanResult:
    """Perform the TLS handshake and collect peer certificate evidence."""

    try:
        context = ssl.create_default_context()

        with socket.create_connection(
            (domain, port),
            timeout=timeout,
        ) as sock:
            with context.wrap_socket(
                sock,
                server_hostname=domain,
            ) as tls:
                cipher = tls.cipher()

                if cipher is None:
                    return _error_result(
                        domain,
                        port,
                        "No cipher suite negotiated",
                        time.perf_counter() - start,
                    )

                der_certificate = tls.getpeercert(binary_form=True)

                if not der_certificate:
                    return _error_result(
                        domain,
                        port,
                        "No certificate returned by server",
                        time.perf_counter() - start,
                    )

                try:
                    certificate_info = parse_certificate(der_certificate)
                except (ValueError, UnsupportedAlgorithm) as error:
                    logger.warning(
                        "Certificate parsing failed for %s:%d: %s",
                        domain,
                        port,
                        error,
                    )
                    return _error_result(
                        domain,
                        port,
                        f"Certificate parsing error: {error}",
                        time.perf_counter() - start,
                    )

                # This is a separate TLS handshake. Its result is evidence
                # from that handshake, not proof of every supported group.
                try:
                    key_group, key_status = collect_key_establishment_group(
                        domain,
                        port=port,
                        timeout=timeout,
                    )
                except (OSError, ValueError, TimeoutError) as error:
                    logger.warning(
                        "Key-establishment probe failed for %s:%d: %s",
                        domain,
                        port,
                        error,
                    )
                    key_group, key_status = None, "unavailable"

                # A source is populated only when a group was actually observed.
                key_source = (
                    "openssl_s_client_separate_handshake"
                    if key_status == "observed" and key_group
                    else None
                )

                return {
                    "domain": domain,
                    "port": port,
                    "scan_status": "success",
                    "tls_version": tls.version(),
                    "cipher_suite": cipher[0],
                    "cipher_strength": cipher[2],
                    **certificate_info,
                    "scan_time_seconds": time.perf_counter() - start,
                    "key_establishment_group": key_group,
                    "key_establishment_evidence_status": key_status,
                    "key_establishment_source": key_source,
                }

    except (OSError, ssl.SSLError) as error:
        return _handle_connection_error(error, domain, port, start)


def scan_domain(
    domain: str,
    port: int = 443,
    timeout: float = 5,
) -> TLSScanResult:
    """Scan one endpoint and return its collected TLS evidence."""

    validation_error = validate_domain_or_error(domain, port)

    if validation_error is not None:
        return validation_error

    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not math.isfinite(timeout)
        or timeout <= 0
    ):
        return _error_result(
            domain,
            port,
            "Invalid timeout",
            0.0,
        )

    logger.info(
        "Starting TLS scan for domain=%s port=%d",
        domain,
        port,
    )

    start = time.perf_counter()

    return _scan_tls_connection(
        domain,
        port,
        float(timeout),
        start,
    )
