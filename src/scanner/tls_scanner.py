"""
TLS Scanner Module
"""

import socket
import ssl
from typing import Any

from cryptography import x509
from cryptography.hazmat.backends import default_backend


def scan_domain(domain: str, port: int = 443, timeout: int = 5) -> dict[str, Any]:
    """
    Perform a real TLS handshake with the given domain and extract metadata.
    """
    context = ssl.create_default_context()

    try:
        with socket.create_connection((domain, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as tls:

                cipher = tls.cipher()
                if cipher is None:
                    return {
                        "domain": domain,
                        "port": port,
                        "error": "No cipher suite negotiated",
                    }

                cert_dict = tls.getpeercert()
                if cert_dict is None:
                    return {
                        "domain": domain,
                        "port": port,
                        "error": "No certificate returned by server",
                    }

                # Extract full DER certificate for real key-size parsing
                der_cert = tls.getpeercert(binary_form=True)
                cert_obj = x509.load_der_x509_certificate(der_cert, default_backend())
                public_key = cert_obj.public_key()

                try:
                    key_size = public_key.key_size
                except AttributeError:
                    key_size = None

                # NOTE:
                # OpenSSL returns subject/issuer as deeply nested tuples.
                # Your original extraction logic is correct and robust.
                # Mypy cannot model this dynamic structure, so we explicitly
                # ignore type-checking for these two generator expressions.
                return {
                    "domain": domain,
                    "port": port,
                    "tls_version": tls.version(),
                    "cipher_suite": cipher[0],
                    "cipher_strength": cipher[2],
                    "certificate_subject": dict(
                        x[0] for x in cert_dict.get("subject", [])
                    ),  # type: ignore[misc]
                    "certificate_issuer": dict(
                        x[0] for x in cert_dict.get("issuer", [])
                    ),  # type: ignore[misc]
                    "not_before": cert_dict.get("notBefore"),
                    "not_after": cert_dict.get("notAfter"),
                    "key_size": key_size,
                }

    except ssl.SSLError as e:
        return {"domain": domain, "port": port, "error": f"SSL error: {e}"}
    except socket.timeout as e:
        return {"domain": domain, "port": port, "error": f"Timeout: {e}"}
    except socket.gaierror as e:
        return {"domain": domain, "port": port, "error": f"DNS error: {e}"}
    except ConnectionError as e:
        return {"domain": domain, "port": port, "error": f"Connection error: {e}"}


if __name__ == "__main__":
    TEST_DOMAIN = "cloudflare.com"
    result = scan_domain(TEST_DOMAIN)
    print(f"Scan result for {TEST_DOMAIN}: {result}")
