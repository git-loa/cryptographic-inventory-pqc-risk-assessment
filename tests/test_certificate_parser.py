"""
Test suite for certificate parser
"""

from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.asymmetric import ec, mldsa, rsa


from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509.oid import NameOID

import pytest

from src.scanner.certificate_parser import (
    parse_certificate,
    _extract_public_key_info,
)
from src.scanner.pqc_scoring import classify_public_key_algorithm


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


def make_test_mldsa_certificate(private_key):
    """Create a self-signed certificate using an ML-DSA private key."""
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(
                NameOID.COMMON_NAME,
                "mldsa-test.example",
            )
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
        .sign(private_key, algorithm=None)
    )

    return certificate.public_bytes(serialization.Encoding.DER)


def test_parse_certificate_identifies_rsa_key():
    """The parser should identify an RSA certificate public key."""

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    der_certificate = make_test_certificate(private_key)
    result = parse_certificate(der_certificate)

    assert result["public_key_algorithm"] == "RSA"
    assert result["key_size"] == 2048
    assert result["public_key_algorithm_oid"] == "1.2.840.113549.1.1.1"
    assert result["certificate_signature_algorithm_oid"] == ("1.2.840.113549.1.1.11")
    assert result["certificate_signature_hash_algorithm"] == "sha256"


def test_parse_certificate_identifies_ec_key():
    """The parser should identify an elliptic-curve certificate public key."""

    private_key = ec.generate_private_key(ec.SECP256R1())

    der_certificate = make_test_certificate(private_key)
    result = parse_certificate(der_certificate)

    assert result["public_key_algorithm"] == "EC"
    assert result["key_size"] == 256
    assert result["public_key_algorithm_oid"] == "1.2.840.10045.2.1"


def test_extract_mldsa44_public_info():
    """Test extraction of public keu info of ML-DSA-44"""
    private_key = mldsa.MLDSA44PrivateKey.generate()

    result = _extract_public_key_info(private_key.public_key())

    assert result["public_key_algorithm"] == "ML-DSA"
    assert result["public_key_variant"] == "ML-DSA-44"
    assert result["key_size"] is None


def test_extract_mldsa65_public_key_info():
    """Test extraction of public keu info of ML-DSA-65"""
    private_key = mldsa.MLDSA65PrivateKey.generate()

    result = _extract_public_key_info(private_key.public_key())

    assert result["public_key_algorithm"] == "ML-DSA"
    assert result["public_key_variant"] == "ML-DSA-65"
    assert result["key_size"] is None


def test_extract_mldsa87_public_key_info():
    """Test extraction of public keu info of ML-DSA-87"""
    private_key = mldsa.MLDSA87PrivateKey.generate()

    result = _extract_public_key_info(private_key.public_key())

    assert result["public_key_algorithm"] == "ML-DSA"
    assert result["public_key_variant"] == "ML-DSA-87"
    assert result["key_size"] is None


@pytest.mark.parametrize(
    ("private_key_factory", "expected_variant", "expected_oid"),
    [
        (
            mldsa.MLDSA44PrivateKey.generate,
            "ML-DSA-44",
            "2.16.840.1.101.3.4.3.17",
        ),
        (
            mldsa.MLDSA65PrivateKey.generate,
            "ML-DSA-65",
            "2.16.840.1.101.3.4.3.18",
        ),
        (
            mldsa.MLDSA87PrivateKey.generate,
            "ML-DSA-87",
            "2.16.840.1.101.3.4.3.19",
        ),
    ],
)
def test_parse_certificate_identifies_mldsa_key(
    private_key_factory,
    expected_variant,
    expected_oid,
):
    """The parser and A1.3 classifier should recognize ML-DSA certificates."""
    private_key = private_key_factory()

    der_certificate = make_test_mldsa_certificate(private_key)
    result = parse_certificate(der_certificate)

    assessment = classify_public_key_algorithm(result["public_key_algorithm"])

    assert result["public_key_algorithm"] == "ML-DSA"
    assert result["public_key_variant"] == expected_variant
    assert result["public_key_algorithm_oid"] == expected_oid

    assert assessment["dimension"] == "public_key_algorithm"
    assert assessment["classification"] == "acceptable"
