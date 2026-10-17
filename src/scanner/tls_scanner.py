"""
TLS Scanner Module
"""

import socket
import ssl
import time


from src.scanner.certificate_parser import parse_certificate

from src.scanner.utils.logger import get_logger
from src.scanner.models import TLSScanResult
from src.scanner.key_establishment import (
    collect_key_establishment_group,
)

logger = get_logger(__name__)


# ------------------------------------------------------------
# Domain Validation
# ------------------------------------------------------------


def validate_domain_or_error(domain: str, port: int = 443) -> TLSScanResult | None:
    """
    Validate domain name and return error result if invalid.
    Returns None if the domain is valid.

    Parameters
    ----------
    domain : str
        The domain name to validate.
    port : int
        The port number for the TLS scan (default is 443).

    Returns
    -------
    TLSScanResult | None
        Returns a TLSScanResult with an error message if the domain is invalid,
        otherwise returns None.
    """

    if not domain or "." not in domain or len(domain) > 253:
        return _error_result(domain, port, "Invalid domain name", 0.0)

    labels = domain.split(".")

    for label in labels:
        if not label or len(label) > 63:
            return _error_result(domain, port, "Invalid domain name", 0.0)
        if label.startswith("-") or label.endswith("-"):
            return _error_result(domain, port, "Invalid domain name", 0.0)
        if any(not (c.isalnum() or c == "-") for c in label):
            return _error_result(domain, port, "Invalid domain name", 0.0)

    return None


# ------------------------------------------------------------
# Error Result Helper
# ------------------------------------------------------------


def _error_result(
    domain: str, port: int, message: str, elapsed: float
) -> TLSScanResult:
    """Return a fully populated TLSScanResult error dict.

    Parameters
    ----------
    domain : str
        The domain name that was scanned.
    port : int
        The port number for the TLS scan (default is 443).
    message : str
        The error message to include in the result.
    elapsed : float
        The time elapsed during the scan.

    Returns
    -------
    TLSScanResult
        A dictionary containing the TLS scan result with an error message.
    """
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
        "scan_time_seconds": elapsed,
        "public_key_algorithm": None,
        "key_establishment_group": None,
        "key_establishment_evidence_status": "unavailable",
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


def _handle_scan_error(
    error: Exception,
    domain: str,
    port: int,
    start: float,
) -> TLSScanResult:
    """Convert a supported connection exception into a scan result."""

    if isinstance(error, ssl.SSLError):
        message = f"SSL error: {error}"
    elif isinstance(error, socket.timeout):
        message = f"Timeout: {error}"
    elif isinstance(error, socket.gaierror):
        message = f"DNS error: {error}"
    else:
        message = f"Connection error: {error}"

    return _error_result(
        domain,
        port,
        message,
        time.perf_counter() - start,
    )


def _scan_tls_connection(
    domain: str,
    port: int,
    timeout: int,
    start: float,
) -> TLSScanResult:
    """Establish a TLS connection and collect certificate metadata."""

    context = ssl.create_default_context()

    try:
        with socket.create_connection((domain, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as tls:

                cipher = tls.cipher()

                if cipher is None:
                    return _error_result(
                        domain,
                        port,
                        "No cipher suite negotiated",
                        time.perf_counter() - start,
                    )

                der_cert = tls.getpeercert(binary_form=True)

                if not der_cert:
                    return _error_result(
                        domain,
                        port,
                        "No certificate returned by server",
                        time.perf_counter() - start,
                    )

                cert_info = parse_certificate(der_cert)

                key_group, key_status = collect_key_establishment_group(
                    domain,
                    port=port,
                    timeout=timeout,
                )

                return {
                    "domain": domain,
                    "port": port,
                    "scan_status": "success",
                    "tls_version": tls.version(),
                    "cipher_suite": cipher[0],
                    "cipher_strength": cipher[2],
                    **cert_info,
                    "scan_time_seconds": time.perf_counter() - start,
                    "key_establishment_group": key_group,
                    "key_establishment_evidence_status": key_status,
                    "key_establishment_source": ("openssl_s_client_separate_handshake"),
                }
    except (
        ssl.SSLError,
        socket.timeout,
        socket.gaierror,
        ConnectionError,
    ) as error:
        return _handle_scan_error(error, domain, port, start)


def scan_domain(
    domain: str,
    port: int = 443,
    timeout: int = 5,
) -> TLSScanResult:
    """Validate a domain and collect its TLS configuration and certificate."""

    validation_error = validate_domain_or_error(domain, port)

    if validation_error:
        return validation_error

    logger.info("Starting TLS scan for domain=%s port=%d", domain, port)

    start = time.perf_counter()

    return _scan_tls_connection(domain, port, timeout, start)
