"""Tests for external asset identifier normalization."""

import pytest

from pqc_inventory.application.assets.identifier_normalization import (
    DNS_NAME_NAMESPACE,
    IP_ADDRESS_NAMESPACE,
    X509_FINGERPRINT_BLAKE2B_512_NAMESPACE,
    X509_FINGERPRINT_BLAKE2S_256_NAMESPACE,
    X509_FINGERPRINT_BLAKE3_256_NAMESPACE,
    X509_FINGERPRINT_SHA1_NAMESPACE,
    X509_FINGERPRINT_SHA256_NAMESPACE,
    X509_FINGERPRINT_SHA384_NAMESPACE,
    X509_FINGERPRINT_SHA512_NAMESPACE,
    X509_FINGERPRINT_SHA3_256_NAMESPACE,
    normalize_dns_name,
    normalize_fingerprint,
    normalize_identifier,
    normalize_ip_address,
)
from pqc_inventory.domain.assets.identifiers import AssetIdentifier

# ---------------------------------------------------------
# DNS normalization
# ---------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("EXAMPLE.COM", "example.com"),
        ("example.com.", "example.com"),
        ("Münich.example", "xn--mnich-kva.example"),
        ("Example.COM.", "example.com"),
    ],
)
def test_normalize_dns_name(value, expected):
    """Normalize DNS names to lowercase ASCII."""

    assert normalize_dns_name(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        " example.com",
        "example.com ",
        "example..com",
        ".example.com",
        "*.example.com",
        "https://example.com",
        "example.com:443",
        "invalid_name.example",
    ],
)
def test_normalize_dns_name_rejects_invalid_values(value):
    """Reject malformed DNS identifiers."""

    with pytest.raises(ValueError):
        normalize_dns_name(value)


def test_normalize_dns_name_rejects_non_string():
    """Require DNS identifiers to be strings."""

    with pytest.raises(TypeError):
        normalize_dns_name(123)


# ---------------------------------------------------------
# IP address normalization
# ---------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("192.0.2.1", "192.0.2.1"),
        ("2001:0db8:0000:0000:0000:0000:0000:0001", "2001:db8::1"),
        ("2001:DB8::1", "2001:db8::1"),
        ("::1", "::1"),
    ],
)
def test_normalize_ip_address(value, expected):
    """Return canonical IPv4 and IPv6 representations."""

    assert normalize_ip_address(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "192.0.2.999",
        "example.com",
        "2001:db8:::1",
        "fe80::1%eth0",
        " 192.0.2.1",
    ],
)
def test_normalize_ip_address_rejects_invalid_values(value):
    """Reject invalid or unsupported IP representations."""

    with pytest.raises(ValueError):
        normalize_ip_address(value)


def test_normalize_ip_address_rejects_non_string():
    """Require IP addresses to be strings."""

    with pytest.raises(TypeError):
        normalize_ip_address(123)


# ---------------------------------------------------------
# Generic fingerprint normalization
# ---------------------------------------------------------


@pytest.mark.parametrize(
    "expected_bytes",
    [20, 32, 48, 64],
)
def test_normalize_fingerprint_accepts_valid_digest_lengths(expected_bytes):
    """Accept hexadecimal fingerprints of the expected length."""

    fingerprint = "AB" * expected_bytes

    assert (
        normalize_fingerprint(
            fingerprint,
            expected_bytes=expected_bytes,
        )
        == "ab" * expected_bytes
    )


def test_normalize_fingerprint_accepts_colon_separated_bytes():
    """Normalize colon-separated hexadecimal bytes."""

    fingerprint = ":".join(["AA"] * 32)

    assert (
        normalize_fingerprint(
            fingerprint,
            expected_bytes=32,
        )
        == "aa" * 32
    )


@pytest.mark.parametrize(
    "value",
    [
        "",
        "AA:BB:C",
        "AA::BB",
        "GG" * 32,
        "A" * 63,
        "A" * 65,
        "AA BB",
        " AA" * 32,
        "AA" * 32 + ":",
    ],
)
def test_normalize_fingerprint_rejects_invalid_values(value):
    """Reject malformed hexadecimal fingerprints."""

    with pytest.raises(ValueError):
        normalize_fingerprint(
            value,
            expected_bytes=32,
        )


def test_normalize_fingerprint_rejects_non_string():
    """Require fingerprints to be strings."""

    with pytest.raises(TypeError):
        normalize_fingerprint(
            123,
            expected_bytes=32,
        )


@pytest.mark.parametrize(
    "expected_bytes",
    [0, -1, True, 32.0],
)
def test_normalize_fingerprint_rejects_invalid_digest_lengths(
    expected_bytes,
):
    """Require a positive integer digest length."""

    with pytest.raises(ValueError):
        normalize_fingerprint(
            "AA" * 32,
            expected_bytes=expected_bytes,
        )


# ---------------------------------------------------------
# X.509 fingerprint profiles
# ---------------------------------------------------------


@pytest.mark.parametrize(
    ("namespace", "digest_bytes"),
    [
        (X509_FINGERPRINT_SHA1_NAMESPACE, 20),
        (X509_FINGERPRINT_SHA256_NAMESPACE, 32),
        (X509_FINGERPRINT_SHA384_NAMESPACE, 48),
        (X509_FINGERPRINT_SHA512_NAMESPACE, 64),
        (X509_FINGERPRINT_SHA3_256_NAMESPACE, 32),
        (X509_FINGERPRINT_BLAKE2S_256_NAMESPACE, 32),
        (X509_FINGERPRINT_BLAKE2B_512_NAMESPACE, 64),
        (X509_FINGERPRINT_BLAKE3_256_NAMESPACE, 32),
    ],
)
def test_normalize_identifier_supports_fingerprint_profiles(
    namespace,
    digest_bytes,
):
    """Normalize fingerprints according to their registered profiles."""

    fingerprint = "AA" * digest_bytes

    identifier = AssetIdentifier(
        namespace=namespace,
        value=fingerprint,
    )

    assert normalize_identifier(identifier) == "aa" * digest_bytes


@pytest.mark.parametrize(
    ("namespace", "digest_bytes"),
    [
        (X509_FINGERPRINT_SHA1_NAMESPACE, 20),
        (X509_FINGERPRINT_SHA256_NAMESPACE, 32),
        (X509_FINGERPRINT_SHA384_NAMESPACE, 48),
        (X509_FINGERPRINT_SHA512_NAMESPACE, 64),
        (X509_FINGERPRINT_SHA3_256_NAMESPACE, 32),
        (X509_FINGERPRINT_BLAKE2S_256_NAMESPACE, 32),
        (X509_FINGERPRINT_BLAKE2B_512_NAMESPACE, 64),
        (X509_FINGERPRINT_BLAKE3_256_NAMESPACE, 32),
    ],
)
def test_normalize_identifier_rejects_incorrect_fingerprint_length(
    namespace,
    digest_bytes,
):
    """Reject fingerprints with incorrect digest lengths."""

    identifier = AssetIdentifier(
        namespace=namespace,
        value="AA" * (digest_bytes - 1),
    )

    with pytest.raises(ValueError):
        normalize_identifier(identifier)


# ---------------------------------------------------------
# Identifier dispatcher
# ---------------------------------------------------------


@pytest.mark.parametrize(
    ("namespace", "value", "expected"),
    [
        (
            DNS_NAME_NAMESPACE,
            "EXAMPLE.COM.",
            "example.com",
        ),
        (
            IP_ADDRESS_NAMESPACE,
            "2001:0DB8::1",
            "2001:db8::1",
        ),
        (
            X509_FINGERPRINT_SHA256_NAMESPACE,
            "AA" * 32,
            "aa" * 32,
        ),
        (
            X509_FINGERPRINT_SHA3_256_NAMESPACE,
            "BB" * 32,
            "bb" * 32,
        ),
    ],
)
def test_normalize_identifier(namespace, value, expected):
    """Dispatch to the correct namespace normalizer."""

    identifier = AssetIdentifier(
        namespace=namespace,
        value=value,
    )

    assert normalize_identifier(identifier) == expected


def test_normalize_identifier_preserves_original_identifier():
    """Normalize without modifying the original identifier."""

    identifier = AssetIdentifier(
        namespace=DNS_NAME_NAMESPACE,
        value="EXAMPLE.COM.",
    )

    normalize_identifier(identifier)

    assert identifier.value == "EXAMPLE.COM."


def test_normalize_identifier_rejects_unsupported_namespace():
    """Reject namespaces without a registered normalizer."""

    identifier = AssetIdentifier(
        namespace="unknown-namespace",
        value="example",
    )

    with pytest.raises(ValueError, match="Unsupported identifier namespace"):
        normalize_identifier(identifier)


def test_normalize_identifier_rejects_invalid_object():
    """Require an AssetIdentifier instance."""

    with pytest.raises(TypeError):
        normalize_identifier("example.com")
