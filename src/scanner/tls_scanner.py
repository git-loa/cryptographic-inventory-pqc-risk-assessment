"""
TLS Scanner Module
"""

import socket
import ssl
import time

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from src.scanner.utils.logger import get_logger
from src.scanner.models import TLSScanResult

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
    }


# ------------------------------------------------------------
# Certificate Parsing
# ------------------------------------------------------------


def parse_certificate(cert_dict, der_cert) -> dict:
    """Extract subject, issuer, validity, and key size
    from certificate.

    Parameters
    ----------
    cert_dict : dict
        The dictionary containing certificate information.
    der_cert : bytes
        The DER-encoded certificate.

    Returns
    -------
    dict
        A dictionary containing the parsed certificate information.
    """
    cert_obj = x509.load_der_x509_certificate(der_cert, default_backend())
    public_key = cert_obj.public_key()

    try:
        key_size = public_key.key_size
    except AttributeError:
        key_size = None

    return {
        "certificate_subject": dict(x[0] for x in cert_dict.get("subject", [])),
        "certificate_issuer": dict(x[0] for x in cert_dict.get("issuer", [])),
        "not_before": cert_dict.get("notBefore"),
        "not_after": cert_dict.get("notAfter"),
        "key_size": key_size,
    }


# ------------------------------------------------------------
# TLS Scanner
# ------------------------------------------------------------


def scan_domain(domain: str, port: int = 443, timeout: int = 5) -> TLSScanResult:
    """
    Perform TLS handshake and return structured TLS metadata.

    Parameters
    ----------
    domain : str
        The domain name to scan.
    port : int, optional
        The port number for the TLS scan (default is 443).
    timeout : int, optional
        The timeout for the TLS scan (default is 5).

    Returns
    -------
    TLSScanResult
        A dictionary containing the TLS scan result.
    """

    # Fast-fail invalid domains
    validation_error = validate_domain_or_error(domain, port)
    if validation_error:
        return validation_error

    logger.info("Starting TLS scan for domain=%s port=%d", domain, port)
    context = ssl.create_default_context()
    start = time.perf_counter()

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

                cert_dict = tls.getpeercert()
                if cert_dict is None:
                    return _error_result(
                        domain,
                        port,
                        "No certificate returned by server",
                        time.perf_counter() - start,
                    )

                der_cert = tls.getpeercert(binary_form=True)
                cert_info = parse_certificate(cert_dict, der_cert)

                elapsed = time.perf_counter() - start

                return {
                    "domain": domain,
                    "port": port,
                    "tls_version": tls.version(),
                    "cipher_suite": cipher[0],
                    "cipher_strength": cipher[2],
                    **cert_info,
                    "scan_time_seconds": elapsed,
                }

    except ssl.SSLError as e:
        return _error_result(
            domain, port, f"SSL error: {e}", time.perf_counter() - start
        )
    except socket.timeout as e:
        return _error_result(domain, port, f"Timeout: {e}", time.perf_counter() - start)
    except socket.gaierror as e:
        return _error_result(
            domain, port, f"DNS error: {e}", time.perf_counter() - start
        )
    except ConnectionError as e:
        return _error_result(
            domain, port, f"Connection error: {e}", time.perf_counter() - start
        )
