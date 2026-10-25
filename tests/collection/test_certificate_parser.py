"""Tests for X.509 certificate metadata extraction."""

import pytest

from cryptography import x509
from src.collection import certificate_parser


def test_parse_rsa_certificate(rsa_certificate):
    """Extract identity, validity, and RSA public-key metadata."""
    result = certificate_parser.parse_certificate(rsa_certificate)

    assert result["certificate_version"] == "v3"
    assert result["certificate_subject"]
    assert result["certificate_issuer"]
    assert result["not_before"]
    assert result["not_after"]

    cert = x509.load_der_x509_certificate(rsa_certificate)
    assert result["certificate_serial_number"] == str(cert.serial_number)

    assert result["public_key_algorithm"] == "RSA"
    assert result["key_size"] == 2048
    assert result["rsa_public_exponent"] == 65537
    assert result["public_key_curve"] is None
    assert result["public_key_variant"] is None

    assert result["public_key_algorithm_oid"]
    assert result["certificate_signature_algorithm_oid"]
    assert result["certificate_signature_hash_algorithm"] == "sha256"


def test_parse_ec_certificate(ec_certificate):
    """Extract EC algorithm and curve metadata."""
    result = certificate_parser.parse_certificate(ec_certificate)

    assert result["public_key_algorithm"] == "EC"
    assert result["public_key_curve"] == "secp256r1"
    assert result["key_size"] == 256
    assert result["rsa_public_exponent"] is None


def test_parse_ed25519_certificate(ed25519_certificate):
    """Extract Ed25519 metadata without reporting a numeric key size."""
    result = certificate_parser.parse_certificate(ed25519_certificate)

    assert result["public_key_algorithm"] == "Ed25519"
    assert result["key_size"] is None
    assert result["public_key_curve"] is None
    assert result["rsa_public_exponent"] is None


def test_parse_mldsa44_certificate(mldsa44_certificate):
    """Identify the ML-DSA-44 public-key variant."""
    result = certificate_parser.parse_certificate(mldsa44_certificate)

    assert result["public_key_algorithm"] == "ML-DSA"
    assert result["public_key_variant"] == "ML-DSA-44"
    assert result["key_size"] is None


def test_parse_mldsa65_certificate(mldsa65_certificate):
    """Identify the ML-DSA-65 public-key variant."""
    result = certificate_parser.parse_certificate(mldsa65_certificate)

    assert result["public_key_algorithm"] == "ML-DSA"
    assert result["public_key_variant"] == "ML-DSA-65"
    assert result["key_size"] is None


def test_parse_mldsa87_certificate(mldsa87_certificate):
    """Identify the ML-DSA-87 public-key variant."""
    result = certificate_parser.parse_certificate(mldsa87_certificate)

    assert result["public_key_algorithm"] == "ML-DSA"
    assert result["public_key_variant"] == "ML-DSA-87"
    assert result["key_size"] is None


def test_parse_certificate_with_extensions(rsa_certificate_with_extensions):
    """Extract SAN, key usage, extended usage, and basic constraints."""
    result = certificate_parser.parse_certificate(rsa_certificate_with_extensions)

    assert "example.com" in result["san_dns_names"]
    assert "www.example.com" in result["san_dns_names"]
    assert "192.0.2.10" in result["san_ip_addresses"]

    assert result["key_usage"] is not None
    assert result["key_usage"]["digital_signature"] is True
    assert result["key_usage"]["key_encipherment"] is True

    assert result["extended_key_usage"] is not None
    assert x509.oid.ExtendedKeyUsageOID.SERVER_AUTH.dotted_string in (
        result["extended_key_usage"]
    )

    assert result["basic_constraints"] == {
        "ca": False,
        "path_length": None,
    }


def test_parse_certificate_without_san(rsa_certificate):
    """Return empty SAN lists when the certificate has no SAN extension."""
    result = certificate_parser.parse_certificate(rsa_certificate)

    assert result["san_dns_names"] == []
    assert result["san_ip_addresses"] == []


def test_parse_certificate_without_usage_extensions(rsa_certificate):
    """Return None for usage extensions absent from the certificate."""
    result = certificate_parser.parse_certificate(rsa_certificate)

    assert result["key_usage"] is None
    assert result["extended_key_usage"] is None
    assert result["basic_constraints"] is None


def test_parse_empty_der_data():
    """Reject empty certificate data."""
    with pytest.raises(ValueError):
        certificate_parser.parse_certificate(b"")


def test_parse_malformed_der_data():
    """Reject data that is not a valid DER-encoded certificate."""
    with pytest.raises(ValueError):
        certificate_parser.parse_certificate(b"not a certificate")
