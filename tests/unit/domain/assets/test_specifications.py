"""Tests for cryptographic asset specifications."""

from datetime import datetime, timedelta, timezone

import pytest

from pqc_inventory.domain.assets.specifications import (
    CertificateSpecification,
    CertificateValidity,
    CryptographicKeySpecification,
    NetworkEndpointSpecification,
    PublicKeyInfo,
    SoftwareComponentSpecification,
)

# ---------------------------------------------------------
# Network endpoint specifications
# ---------------------------------------------------------


def test_create_network_endpoint_specification():
    """Create a valid network endpoint specification."""

    specification = NetworkEndpointSpecification(
        service_protocol="https",
        port=443,
    )

    assert specification.service_protocol == "https"
    assert specification.port == 443
    assert specification.transport_protocol == "tcp"


def test_network_endpoint_accepts_custom_transport_protocol():
    """Allow an explicitly specified transport protocol."""

    specification = NetworkEndpointSpecification(
        service_protocol="https",
        port=443,
        transport_protocol="udp",
    )

    assert specification.transport_protocol == "udp"


@pytest.mark.parametrize(
    "port",
    [0, -1, 65536, True, "443"],
)
def test_invalid_network_endpoint_port_is_rejected(port):
    """Reject invalid network endpoint ports."""

    with pytest.raises(ValueError):
        NetworkEndpointSpecification(
            service_protocol="https",
            port=port,
        )


@pytest.mark.parametrize(
    "field_name",
    ["service_protocol", "transport_protocol"],
)
@pytest.mark.parametrize(
    "value",
    ["", "   "],
)
def test_empty_network_protocol_is_rejected(field_name, value):
    """Reject empty protocol names."""

    attributes = {
        "service_protocol": "https",
        "port": 443,
        "transport_protocol": "tcp",
    }

    attributes[field_name] = value

    with pytest.raises(ValueError):
        NetworkEndpointSpecification(**attributes)


@pytest.mark.parametrize(
    "field_name",
    ["service_protocol", "transport_protocol"],
)
@pytest.mark.parametrize(
    "value",
    [None, 123],
)
def test_non_string_network_protocol_is_rejected(field_name, value):
    """Require protocol names to be strings."""

    attributes = {
        "service_protocol": "https",
        "port": 443,
        "transport_protocol": "tcp",
    }

    attributes[field_name] = value

    with pytest.raises(TypeError):
        NetworkEndpointSpecification(**attributes)


# ---------------------------------------------------------
# Certificate validity
# ---------------------------------------------------------


def test_create_certificate_validity():
    """Create a valid certificate validity period."""

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2027, 1, 1, tzinfo=timezone.utc)

    validity = CertificateValidity(
        not_before=start,
        not_after=end,
    )

    assert validity.not_before == start
    assert validity.not_after == end


def test_certificate_validity_allows_unknown_dates():
    """Allow certificate validity dates to be unavailable."""

    validity = CertificateValidity()

    assert validity.not_before is None
    assert validity.not_after is None


def test_certificate_validity_allows_one_known_date():
    """Allow partially available validity information."""

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    validity = CertificateValidity(
        not_before=start,
    )

    assert validity.not_before == start
    assert validity.not_after is None


def test_certificate_validity_rejects_reversed_dates():
    """Reject a validity period with reversed dates."""

    start = datetime(2027, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="not_before"):
        CertificateValidity(
            not_before=start,
            not_after=end,
        )


@pytest.mark.parametrize(
    "date",
    [
        datetime(2026, 1, 1),
        "2026-01-01T00:00:00Z",
        123,
    ],
)
def test_certificate_validity_requires_aware_datetime(date):
    """Reject invalid or timezone-naive validity dates."""

    with pytest.raises((TypeError, ValueError)):
        CertificateValidity(not_before=date)


def test_certificate_validity_is_immutable():
    """Prevent modification of certificate validity dates."""

    validity = CertificateValidity(
        not_before=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    with pytest.raises(AttributeError):
        validity.not_before = datetime(
            2027,
            1,
            1,
            tzinfo=timezone.utc,
        )


# ---------------------------------------------------------
# Public key information
# ---------------------------------------------------------


def test_create_public_key_info():
    """Create public-key metadata."""

    public_key = PublicKeyInfo(
        algorithm="RSA",
        key_size_bits=2048,
    )

    assert public_key.algorithm == "RSA"
    assert public_key.key_size_bits == 2048
    assert public_key.curve is None


def test_create_elliptic_curve_public_key_info():
    """Describe an elliptic-curve public key."""

    public_key = PublicKeyInfo(
        algorithm="ECDSA",
        curve="secp256r1",
    )

    assert public_key.algorithm == "ECDSA"
    assert public_key.key_size_bits is None
    assert public_key.curve == "secp256r1"


def test_public_key_info_allows_missing_optional_metadata():
    """Allow unknown public-key size and curve information."""

    public_key = PublicKeyInfo(
        algorithm="ML-DSA-65",
    )

    assert public_key.key_size_bits is None
    assert public_key.curve is None


@pytest.mark.parametrize(
    "algorithm",
    ["", "   "],
)
def test_public_key_info_rejects_empty_algorithm(algorithm):
    """Reject an empty public-key algorithm."""

    with pytest.raises(ValueError, match="algorithm"):
        PublicKeyInfo(algorithm=algorithm)


@pytest.mark.parametrize(
    "algorithm",
    [None, 123],
)
def test_public_key_info_rejects_non_string_algorithm(algorithm):
    """Require a string public-key algorithm."""

    with pytest.raises(TypeError, match="algorithm"):
        PublicKeyInfo(algorithm=algorithm)


@pytest.mark.parametrize(
    "key_size",
    [0, -1, True, "2048"],
)
def test_public_key_info_rejects_invalid_key_size(key_size):
    """Reject invalid public-key sizes."""

    with pytest.raises(ValueError, match="key_size_bits"):
        PublicKeyInfo(
            algorithm="RSA",
            key_size_bits=key_size,
        )


def test_public_key_info_is_immutable():
    """Prevent modification of public-key information."""

    public_key = PublicKeyInfo(
        algorithm="RSA",
        key_size_bits=2048,
    )

    with pytest.raises(AttributeError):
        public_key.key_size_bits = 4096


# ---------------------------------------------------------
# Certificate specifications
# ---------------------------------------------------------


def test_create_certificate_specification():
    """Create a certificate specification with nested metadata."""

    now = datetime.now(timezone.utc)

    validity = CertificateValidity(
        not_before=now,
        not_after=now + timedelta(days=365),
    )

    public_key = PublicKeyInfo(
        algorithm="RSA",
        key_size_bits=2048,
    )

    specification = CertificateSpecification(
        serial_number="123456789",
        subject="CN=example.com",
        issuer="CN=Example CA",
        validity=validity,
        signature_algorithm="sha256WithRSAEncryption",
        public_key=public_key,
    )

    assert specification.serial_number == "123456789"
    assert specification.subject == "CN=example.com"
    assert specification.issuer == "CN=Example CA"
    assert specification.validity == validity
    assert specification.public_key == public_key


def test_certificate_specification_allows_missing_metadata():
    """Allow unavailable certificate metadata."""

    specification = CertificateSpecification(
        serial_number="123456789",
    )

    assert specification.subject is None
    assert specification.issuer is None
    assert specification.validity is None
    assert specification.signature_algorithm is None
    assert specification.public_key is None


@pytest.mark.parametrize(
    "serial_number",
    ["", "   "],
)
def test_certificate_specification_rejects_empty_serial_number(
    serial_number,
):
    """Reject empty certificate serial numbers."""

    with pytest.raises(ValueError, match="serial_number"):
        CertificateSpecification(serial_number=serial_number)


@pytest.mark.parametrize(
    "field_name",
    ["subject", "issuer", "signature_algorithm"],
)
def test_certificate_specification_rejects_empty_optional_text(
    field_name,
):
    """Reject empty strings in optional certificate metadata."""

    with pytest.raises(ValueError):
        CertificateSpecification(
            serial_number="123456789",
            **{field_name: "   "},
        )


def test_certificate_specification_rejects_invalid_validity():
    """Require a CertificateValidity instance."""

    with pytest.raises(TypeError, match="CertificateValidity"):
        CertificateSpecification(
            serial_number="123456789",
            validity="invalid",
        )


def test_certificate_specification_rejects_invalid_public_key():
    """Require a PublicKeyInfo instance."""

    with pytest.raises(TypeError, match="PublicKeyInfo"):
        CertificateSpecification(
            serial_number="123456789",
            public_key="invalid",
        )


def test_certificate_specification_is_immutable():
    """Prevent modification of certificate metadata."""

    specification = CertificateSpecification(
        serial_number="123456789",
    )

    with pytest.raises(AttributeError):
        specification.serial_number = "987654321"


# ---------------------------------------------------------
# Software component specifications
# ---------------------------------------------------------


def test_create_software_component_specification():
    """Create software component metadata."""

    specification = SoftwareComponentSpecification(
        name="OpenSSL",
        version="3.5.5",
        vendor="OpenSSL Project",
        ecosystem="system_package",
    )

    assert specification.name == "OpenSSL"
    assert specification.version == "3.5.5"
    assert specification.vendor == "OpenSSL Project"
    assert specification.ecosystem == "system_package"


def test_software_component_allows_missing_metadata():
    """Allow unknown optional software component metadata."""

    specification = SoftwareComponentSpecification(
        name="OpenSSL",
    )

    assert specification.version is None
    assert specification.vendor is None
    assert specification.ecosystem is None


@pytest.mark.parametrize(
    "name",
    ["", "   "],
)
def test_software_component_rejects_empty_name(name):
    """Require a non-empty software component name."""

    with pytest.raises(ValueError, match="name"):
        SoftwareComponentSpecification(name=name)


def test_software_component_is_immutable():
    """Prevent modification of software component metadata."""

    specification = SoftwareComponentSpecification(
        name="OpenSSL",
        version="3.5.5",
    )

    with pytest.raises(AttributeError):
        specification.version = "3.6.0"


# ---------------------------------------------------------
# Cryptographic key specifications
# ---------------------------------------------------------


def test_create_cryptographic_key_specification():
    """Create cryptographic key metadata."""

    specification = CryptographicKeySpecification(
        algorithm="RSA",
        key_size_bits=2048,
        key_usage=("digital_signature", "key_encipherment"),
    )

    assert specification.algorithm == "RSA"
    assert specification.key_size_bits == 2048
    assert specification.curve is None
    assert specification.key_usage == (
        "digital_signature",
        "key_encipherment",
    )


def test_cryptographic_key_allows_missing_optional_metadata():
    """Allow unavailable key size and curve information."""

    specification = CryptographicKeySpecification(
        algorithm="ML-KEM-768",
    )

    assert specification.key_size_bits is None
    assert specification.curve is None
    assert not specification.key_usage


def test_cryptographic_key_usage_requires_tuple():
    """Require immutable key usage collections."""

    with pytest.raises(TypeError, match="key_usage"):
        CryptographicKeySpecification(
            algorithm="RSA",
            key_usage=["digital_signature"],
        )


@pytest.mark.parametrize(
    "usage",
    ["", "   "],
)
def test_cryptographic_key_rejects_empty_usage(usage):
    """Reject empty key usage entries."""

    with pytest.raises(ValueError):
        CryptographicKeySpecification(
            algorithm="RSA",
            key_usage=(usage,),
        )


def test_cryptographic_key_rejects_non_string_usage():
    """Require key usage entries to be strings."""

    with pytest.raises(TypeError):
        CryptographicKeySpecification(
            algorithm="RSA",
            key_usage=(123,),
        )


def test_cryptographic_key_size_must_be_positive():
    """Reject invalid cryptographic key sizes."""

    with pytest.raises(ValueError):
        CryptographicKeySpecification(
            algorithm="RSA",
            key_size_bits=0,
        )


def test_cryptographic_key_specification_is_immutable():
    """Prevent modification of cryptographic key metadata."""

    specification = CryptographicKeySpecification(
        algorithm="RSA",
        key_size_bits=2048,
    )

    with pytest.raises(AttributeError):
        specification.algorithm = "ECDSA"
