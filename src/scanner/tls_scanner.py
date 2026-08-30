"""
TLS Scanner Module
"""

import socket
import ssl

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from src.scanner.utils.logger import get_logger
from src.scanner.models import TLSScanResult

logger = get_logger(__name__)


def scan_domain(domain: str, port: int = 443, timeout: int = 5) -> TLSScanResult:
    """
    Perform a real TLS handshake with the target domain and extract
    connection and certificate metadata.

    The function establishes a TCP connection, negotiates a TLS session,
    and returns structured information including:

    - negotiated TLS version
    - cipher suite and key strength
    - certificate subject and issuer fields
    - certificate validity period (notBefore / notAfter)
    - public‑key size extracted from the DER certificate

    If the handshake fails (e.g., SSL error, DNS failure, timeout,
    missing certificate, or no negotiated cipher), the function returns
    a TLSScanResult containing an appropriate error message.

    Parameters
    ----------
    domain : str
        The domain name to scan.
    port : int, optional
        The TLS port to connect to (default: 443).
    timeout : int, optional
        Timeout in seconds for the TCP connection.

    Returns
    -------
    TLSScanResult
        A dictionary-like object containing TLS metadata or an error
        description if the handshake could not be completed.
    """

    logger.info("Starting TLS scan for domain=%s port=%d", domain, port)
    logger.debug("Creating TLS context using default settings")

    context = ssl.create_default_context()

    try:
        logger.debug(
            "Attempting to create TCP connection to %s:%d with timeout=%d",
            domain,
            port,
            timeout,
        )
        with socket.create_connection((domain, port), timeout=timeout) as sock:
            logger.debug("Wrapping socket with TLS context for domain=%s", domain)
            with context.wrap_socket(sock, server_hostname=domain) as tls:
                cipher = tls.cipher()
                if cipher is None:
                    logger.warning("No cipher suite negotiated for domain=%s", domain)
                    return {
                        "domain": domain,
                        "port": port,
                        "error": "No cipher suite negotiated",
                    }

                cert_dict = tls.getpeercert()
                logger.debug(
                    "Certificate retrieved for domain=%s: %s", domain, cert_dict
                )

                if cert_dict is None:
                    logger.warning(
                        "No certificate returned by server for domain=%s", domain
                    )
                    return {
                        "domain": domain,
                        "port": port,
                        "error": "No certificate returned by server",
                    }

                # Extract full DER certificate for real key-size parsing
                logger.debug("Retrieving DER certificate for domain=%s", domain)
                der_cert = tls.getpeercert(binary_form=True)
                cert_obj = x509.load_der_x509_certificate(der_cert, default_backend())
                public_key = cert_obj.public_key()

                try:
                    key_size = public_key.key_size
                    logger.debug(
                        "Extracted key size for domain=%s: %d bits", domain, key_size
                    )
                except AttributeError:
                    key_size = None
                    logger.debug(
                        "Public key does not have a key_size attribute for domain=%s",
                        domain,
                    )

                scanned_result: TLSScanResult = {
                    "domain": domain,
                    "port": port,
                    "tls_version": tls.version(),
                    "cipher_suite": cipher[0],
                    "cipher_strength": cipher[2],
                    "certificate_subject": dict(
                        x[0] for x in cert_dict.get("subject", [])
                    ),
                    "certificate_issuer": dict(
                        x[0] for x in cert_dict.get("issuer", [])
                    ),
                    "not_before": cert_dict.get("notBefore"),
                    "not_after": cert_dict.get("notAfter"),
                    "key_size": key_size,
                }

            logger.info(
                "TLS scan completed for domain=%s (TLS=%s, cipher=%s)",
                domain,
                scanned_result["tls_version"],
                scanned_result["cipher_suite"],
            )
            logger.debug(
                "Full TLS scan result for domain=%s: %s", domain, scanned_result
            )

            return scanned_result

    except ssl.SSLError as e:
        logger.error("SSL error during handshake with domain=%s: %s", domain, e)
        return {"domain": domain, "port": port, "error": f"SSL error: {e}"}
    except socket.timeout as e:
        logger.error("Timeout during connection to domain=%s:%d:  %s", domain, port, e)
        return {"domain": domain, "port": port, "error": f"Timeout: {e}"}
    except socket.gaierror as e:
        logger.error("DNS resolution error for domain=%s: %s", domain, e)
        return {"domain": domain, "port": port, "error": f"DNS error: {e}"}
    except ConnectionError as e:
        logger.error("Connection error for domain=%s:%d: %s", domain, port, e)
        return {"domain": domain, "port": port, "error": f"Connection error: {e}"}
