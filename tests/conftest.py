"""Shared pytest fixtures for cryptographic inventory tests."""

# Pytest fixture injection intentionally uses fixture names as parameters.
# pylint: disable=redefined-outer-name


import ipaddress
from datetime import datetime, timedelta, timezone

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, mldsa, rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

# ---------------------------------------------------------------------------
# Shared test constants
# ---------------------------------------------------------------------------

TEST_DOMAIN = "example.com"
TEST_DOMAIN_ALT = "www.example.com"

TEST_IPV4 = "192.0.2.10"
TEST_IPV6 = "2001:db8::10"

TEST_PORT = 443

RSA_KEY_SIZE = 2048
RSA_PUBLIC_EXPONENT = 65537

EC_TEST_CURVE = ec.SECP256R1()


# ---------------------------------------------------------------------------
# Private-key fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def rsa_private_key():
    """Generate an RSA private key for testing."""
    return rsa.generate_private_key(
        public_exponent=RSA_PUBLIC_EXPONENT,
        key_size=RSA_KEY_SIZE,
    )


@pytest.fixture
def ec_private_key():
    """Generate an elliptic-curve private key for testing."""
    return ec.generate_private_key(EC_TEST_CURVE)


@pytest.fixture
def ed25519_private_key():
    """Generate an Ed25519 private key for testing."""
    return ed25519.Ed25519PrivateKey.generate()


@pytest.fixture
def mldsa44_private_key():
    """Generate an ML-DSA-44 private key for testing."""
    return mldsa.MLDSA44PrivateKey.generate()


@pytest.fixture
def mldsa65_private_key():
    """Generate an ML-DSA-65 private key for testing."""
    return mldsa.MLDSA65PrivateKey.generate()


@pytest.fixture
def mldsa87_private_key():
    """Generate an ML-DSA-87 private key for testing."""
    return mldsa.MLDSA87PrivateKey.generate()


# ---------------------------------------------------------------------------
# Certificate factory
# ---------------------------------------------------------------------------


@pytest.fixture
def certificate_factory():
    """Return a factory that creates DER-encoded X.509 test certificates."""

    def _create_certificate(
        private_key,
        *,
        common_name=TEST_DOMAIN,
        include_extensions=False,
        serial_number=None,
    ):
        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
                x509.NameAttribute(
                    NameOID.ORGANIZATION_NAME,
                    "Cryptographic Inventory Test",
                ),
            ]
        )

        now = datetime.now(timezone.utc)

        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(private_key.public_key())
            .serial_number(
                serial_number
                if serial_number is not None
                else x509.random_serial_number()
            )
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=30))
        )

        if include_extensions:
            builder = builder.add_extension(
                x509.SubjectAlternativeName(
                    [
                        x509.DNSName(TEST_DOMAIN),
                        x509.DNSName(TEST_DOMAIN_ALT),
                        x509.IPAddress(ipaddress.ip_address(TEST_IPV4)),
                        x509.IPAddress(ipaddress.ip_address(TEST_IPV6)),
                    ]
                ),
                critical=False,
            )

            builder = builder.add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=True,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=None,
                    decipher_only=None,
                ),
                critical=True,
            )

            builder = builder.add_extension(
                x509.ExtendedKeyUsage(
                    [
                        ExtendedKeyUsageOID.SERVER_AUTH,
                        ExtendedKeyUsageOID.CLIENT_AUTH,
                    ]
                ),
                critical=False,
            )

            builder = builder.add_extension(
                x509.BasicConstraints(
                    ca=False,
                    path_length=None,
                ),
                critical=True,
            )

        # ML-DSA uses algorithm=None in supported cryptography versions.
        # RSA, EC, and Ed25519 use their respective signing configurations.
        if isinstance(
            private_key,
            (
                mldsa.MLDSA44PrivateKey,
                mldsa.MLDSA65PrivateKey,
                mldsa.MLDSA87PrivateKey,
            ),
        ):
            signature_algorithm = None
        elif isinstance(private_key, ed25519.Ed25519PrivateKey):
            signature_algorithm = None
        else:
            signature_algorithm = hashes.SHA256()

        certificate = builder.sign(
            private_key=private_key,
            algorithm=signature_algorithm,
        )

        return certificate.public_bytes(serialization.Encoding.DER)

    return _create_certificate


# ---------------------------------------------------------------------------
# DER-encoded X.509 certificate fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def rsa_certificate(rsa_private_key, certificate_factory):
    """Return a DER-encoded certificate with an RSA public key."""
    return certificate_factory(rsa_private_key)


@pytest.fixture
def rsa_certificate_with_extensions(rsa_private_key, certificate_factory):
    """Return an RSA certificate containing common X.509 extensions."""
    return certificate_factory(
        rsa_private_key,
        include_extensions=True,
    )


@pytest.fixture
def ec_certificate(ec_private_key, certificate_factory):
    """Return a DER-encoded certificate with an EC public key."""
    return certificate_factory(ec_private_key)


@pytest.fixture
def ed25519_certificate(ed25519_private_key, certificate_factory):
    """Return a DER-encoded certificate with an Ed25519 public key."""
    return certificate_factory(ed25519_private_key)


@pytest.fixture
def mldsa44_certificate(mldsa44_private_key, certificate_factory):
    """Return a DER-encoded certificate with an ML-DSA-44 public key."""
    return certificate_factory(mldsa44_private_key)


@pytest.fixture
def mldsa65_certificate(mldsa65_private_key, certificate_factory):
    """Return a DER-encoded certificate with an ML-DSA-65 public key."""
    return certificate_factory(mldsa65_private_key)


@pytest.fixture
def mldsa87_certificate(mldsa87_private_key, certificate_factory):
    """Return a DER-encoded certificate with an ML-DSA-87 public key."""
    return certificate_factory(mldsa87_private_key)
