"""Smoke tests for shared cryptographic test fixtures."""

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, mldsa, rsa


@pytest.mark.parametrize(
    ("fixture_name", "expected_key_type"),
    [
        ("rsa_certificate", rsa.RSAPublicKey),
        ("rsa_certificate_with_extensions", rsa.RSAPublicKey),
        ("ec_certificate", ec.EllipticCurvePublicKey),
        ("ed25519_certificate", ed25519.Ed25519PublicKey),
        ("mldsa44_certificate", mldsa.MLDSA44PublicKey),
        ("mldsa65_certificate", mldsa.MLDSA65PublicKey),
        ("mldsa87_certificate", mldsa.MLDSA87PublicKey),
    ],
)
def test_certificate_fixtures_produce_valid_der(
    request,
    fixture_name,
    expected_key_type,
):
    """Each certificate fixture should produce parseable DER and the expected key."""
    der_certificate = request.getfixturevalue(fixture_name)

    certificate = x509.load_der_x509_certificate(der_certificate)

    assert isinstance(der_certificate, bytes)
    assert len(der_certificate) > 0
    assert isinstance(certificate.public_key(), expected_key_type)


def test_rsa_certificate_with_extensions_contains_expected_extensions(
    rsa_certificate_with_extensions,
):
    """The extended RSA certificate should contain its configured extensions."""
    certificate = x509.load_der_x509_certificate(rsa_certificate_with_extensions)

    assert certificate.extensions.get_extension_for_class(x509.SubjectAlternativeName)

    assert certificate.extensions.get_extension_for_class(x509.KeyUsage)

    assert certificate.extensions.get_extension_for_class(x509.ExtendedKeyUsage)

    assert certificate.extensions.get_extension_for_class(x509.BasicConstraints)


def test_rsa_certificate_without_extensions_has_no_extensions(
    rsa_certificate,
):
    """The basic RSA certificate should not contain optional extensions."""
    certificate = x509.load_der_x509_certificate(rsa_certificate)

    assert len(certificate.extensions) == 0
