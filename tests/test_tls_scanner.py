"""
Unit tests for the TLS scanner module.
"""

from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import NameOID
from src.scanner.tls_scanner import parse_certificate, scan_domain


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


def make_test_certificate(private_key):
    """Create a self-signed certificate for testing."""

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "test.example"),
        ]
    )

    now = datetime.now(timezone.utc)

    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=30))
        .sign(private_key, hashes.SHA256())
    )

    return certificate.public_bytes(serialization.Encoding.DER)


def test_parse_certificate_identifies_rsa_key():
    """The parser should identify an RSA certificate public key."""

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    der_certificate = make_test_certificate(private_key)
    result = parse_certificate({}, der_certificate)

    assert result["public_key_algorithm"] == "RSA"
    assert result["key_size"] == 2048


def test_parse_certificate_identifies_ec_key():
    """The parser should identify an elliptic-curve certificate public key."""

    private_key = ec.generate_private_key(ec.SECP256R1())

    der_certificate = make_test_certificate(private_key)
    result = parse_certificate({}, der_certificate)

    assert result["public_key_algorithm"] == "EC"
    assert result["key_size"] == 256
