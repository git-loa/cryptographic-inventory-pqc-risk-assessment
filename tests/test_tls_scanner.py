"""
Unit tests for the TLS scanner module.
"""

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
