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

                # Cipher suite (may be None)
                cipher = tls.cipher()
                if cipher is None:
                    cipher_suite: str | None = None
                    cipher_strength: int | None = None
                else:
                    cipher_suite = cipher[0]
                    cipher_strength = cipher[2]

                # Certificate dict (may be None)
                cert_dict = tls.getpeercert()
                if cert_dict is None:
                    return {
                        "domain": domain,
                        "port": port,
                        "error": "No certificate returned by server",
                    }

                # DER certificate for key size
                der_cert = tls.getpeercert(binary_form=True)
                cert_obj = x509.load_der_x509_certificate(der_cert, default_backend())
                public_key = cert_obj.public_key()

                try:
                    key_size = public_key.key_size
                except AttributeError:
                    key_size = None

                # -----------------------------
                # Subject extraction
                # -----------------------------
                raw_subject_any: object = cert_dict.get("subject", [])
                raw_subject: list[tuple[tuple[tuple[str, str], ...], ...]] = (
                    raw_subject_any if isinstance(raw_subject_any, list) else []
                )

                subject: dict[str, str] = {}
                for entry in raw_subject:
                    if (
                        isinstance(entry, tuple)
                        and len(entry) > 0
                        and isinstance(entry[0], tuple)
                        and len(entry[0]) > 0
                        and isinstance(entry[0][0], tuple)
                        and len(entry[0][0]) == 2
                    ):
                        k, v = entry[0][0]
                        subject[k] = v

                # -----------------------------
                # Issuer extraction
                # -----------------------------
                raw_issuer_any: object = cert_dict.get("issuer", [])
                raw_issuer: list[tuple[tuple[tuple[str, str], ...], ...]] = (
                    raw_issuer_any if isinstance(raw_issuer_any, list) else []
                )

                issuer: dict[str, str] = {}
                for entry in raw_issuer:
                    if (
                        isinstance(entry, tuple)
                        and len(entry) > 0
                        and isinstance(entry[0], tuple)
                        and len(entry[0]) > 0
                        and isinstance(entry[0][0], tuple)
                        and len(entry[0][0]) == 2
                    ):
                        k, v = entry[0][0]
                        issuer[k] = v

                return {
                    "domain": domain,
                    "port": port,
                    "tls_version": tls.version(),
                    "cipher_suite": cipher_suite,
                    "cipher_strength": cipher_strength,
                    "certificate_subject": subject,
                    "certificate_issuer": issuer,
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
