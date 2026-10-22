"""
Unit tests for the TLS scanner module.
"""

from unittest.mock import MagicMock, patch

from src.scanner.tls_scanner import scan_domain


def test_scan_domain(all_domains):
    """
    Test the scan_domain function with a sample domain.
    """
    sample_domain = all_domains[0]
    result = scan_domain(sample_domain)

    assert isinstance(result, dict)
    assert result["domain"] == sample_domain
    assert "tls_version" in result or "error" in result


def test_scan_domain_valid_domain():
    """
    Test scan_domain with a known valid domain.
    """
    domain = "google.com"
    result = scan_domain(domain)

    assert isinstance(result, dict)
    assert result["domain"] == domain

    # Valid TLS scan should produce version + cipher suite
    assert "tls_version" in result
    assert result["tls_version"] is not None
    assert "cipher_suite" in result
    assert result["cipher_suite"] is not None


def test_scan_domain_invalid_domain():
    """
    Test scan_domain with an invalid domain to ensure proper error handling.
    """
    domain = "invalid-domain.example"
    result = scan_domain(domain)

    assert isinstance(result, dict)
    assert result["domain"] == domain
    assert "error" in result
    assert isinstance(result["error"], str)
    assert result["error"].strip() != ""

    valid_error_fragments = [
        "dns error",  # socket.gaierror
        "getaddrinfo",  # Windows DNS error
        "ssl error",  # ssl.SSLError
        "handshake",  # TLS handshake failure
        "timeout",  # socket.timeout
        "connection error",  # ConnectionError
        "refused",  # TCP refused
    ]

    error_lower = result["error"].lower()
    assert any(fragment in error_lower for fragment in valid_error_fragments)


def test_successful_tls_scan_has_success_status():
    """A successful TLS handshake should report a success status."""

    fake_tls = MagicMock()
    fake_tls.cipher.return_value = (
        "TLS_AES_256_GCM_SHA384",
        "TLSv1.3",
        256,
    )
    fake_tls.version.return_value = "TLSv1.3"
    fake_tls.getpeercert.return_value = b"fake-certificate-der"

    fake_context = MagicMock()
    fake_context.wrap_socket.return_value.__enter__.return_value = fake_tls

    with (
        patch(
            "src.scanner.tls_scanner.validate_domain_or_error",
            return_value=None,
        ),
        patch(
            "src.scanner.tls_scanner.ssl.create_default_context",
            return_value=fake_context,
        ),
        patch("src.scanner.tls_scanner.socket.create_connection") as mock_connect,
        patch(
            "src.scanner.tls_scanner.parse_certificate",
            return_value={
                "certificate_subject": {},
                "certificate_issuer": {},
                "not_before": None,
                "not_after": None,
                "key_size": 2048,
                "public_key_algorithm": "RSA",
            },
        ),
        patch(
            "src.scanner.tls_scanner.collect_key_establishment_group",
            return_value=("X25519", "observed"),
        ),
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()

        result = scan_domain("example.com")

    assert result["scan_status"] == "success"
    assert "error" not in result


def test_unexpected_os_error_returns_failed_status():
    """An unexpected OSError should produce a structured failure result."""
    with (
        patch(
            "src.scanner.tls_scanner.validate_domain_or_error",
            return_value=None,
        ),
        patch(
            "src.scanner.tls_scanner.socket.create_connection",
            side_effect=OSError("Unexpected socket failure"),
        ),
    ):
        result = scan_domain("example.com")

    assert result["scan_status"] == "failed"
    assert "error" in result
    assert "Unexpected socket failure" in result["error"]


def test_failed_tls_scan_has_failed_status():
    """A failed TLS connection should report a failed status."""

    with (
        patch(
            "src.scanner.tls_scanner.validate_domain_or_error",
            return_value=None,
        ),
        patch(
            "src.scanner.tls_scanner.socket.create_connection",
            side_effect=ConnectionError("Connection refused"),
        ),
    ):
        result = scan_domain("example.com")

    assert result["scan_status"] == "failed"
    assert result["error"]
