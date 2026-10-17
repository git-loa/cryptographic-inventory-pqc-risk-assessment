from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.asymmetric import ec, rsa


from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509.oid import NameOID
from src.scanner.certificate_parser import parse_certificate


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
