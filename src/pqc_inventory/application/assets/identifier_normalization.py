"""Normalize external asset identifiers for identity comparison."""

import ipaddress
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

import idna

from pqc_inventory.domain.assets.identifiers import AssetIdentifier

DNS_NAME_NAMESPACE = "dns-name"
IP_ADDRESS_NAMESPACE = "ip-address"

X509_FINGERPRINT_SHA1_NAMESPACE = "x509-fingerprint-sha1"
X509_FINGERPRINT_SHA256_NAMESPACE = "x509-fingerprint-sha256"
X509_FINGERPRINT_SHA384_NAMESPACE = "x509-fingerprint-sha384"
X509_FINGERPRINT_SHA512_NAMESPACE = "x509-fingerprint-sha512"
X509_FINGERPRINT_SHA3_256_NAMESPACE = "x509-fingerprint-sha3-256"
X509_FINGERPRINT_BLAKE2S_256_NAMESPACE = "x509-fingerprint-blake2s-256"
X509_FINGERPRINT_BLAKE2B_512_NAMESPACE = "x509-fingerprint-blake2b-512"
X509_FINGERPRINT_BLAKE3_256_NAMESPACE = "x509-fingerprint-blake3-256"


def _require_identifier_text(value: str, field_name: str) -> str:
    """Require non-empty text without surrounding whitespace."""

    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")

    if not value:
        raise ValueError(f"{field_name} cannot be empty.")

    if value != value.strip():
        raise ValueError(f"{field_name} cannot contain surrounding whitespace.")

    return value


# ---------------------------------------------------------
# DNS and IP address normalization
# ---------------------------------------------------------


def normalize_dns_name(value: str) -> str:
    """Return the canonical ASCII representation of a DNS name."""

    hostname = _require_identifier_text(value, "DNS name")

    if any(character.isspace() for character in hostname):
        raise ValueError("DNS name cannot contain whitespace.")

    if hostname.endswith("."):
        hostname = hostname[:-1]

    if not hostname or len(hostname) > 253:
        raise ValueError("DNS name must contain between 1 and 253 characters.")

    if "*" in hostname:
        raise ValueError("Wildcard DNS names are not valid asset identifiers.")

    try:
        normalized = (
            idna.encode(
                hostname,
                uts46=True,
                std3_rules=True,
            )
            .decode("ascii")
            .lower()
        )
    except idna.IDNAError as error:
        raise ValueError(f"Invalid DNS name: {value!r}.") from error

    labels = normalized.split(".")

    if any(not label for label in labels):
        raise ValueError("DNS name cannot contain empty labels.")

    if len(normalized) > 253:
        raise ValueError("Normalized DNS name exceeds 253 characters.")

    return normalized


def normalize_ip_address(value: str) -> str:
    """Return the canonical representation of an IPv4 or IPv6 address."""

    address = _require_identifier_text(value, "IP address")

    if "%" in address:
        raise ValueError("Scoped IP addresses are not supported.")

    try:
        return str(ipaddress.ip_address(address))
    except ValueError as error:
        raise ValueError(f"Invalid IP address: {value!r}.") from error


# ---------------------------------------------------------
# Generic fingerprint normalization
# ---------------------------------------------------------


def normalize_fingerprint(
    value: str,
    *,
    expected_bytes: int,
) -> str:
    """Normalize a hexadecimal fingerprint.

    Supports contiguous hexadecimal values and colon-separated
    hexadecimal bytes.

    The returned fingerprint is lowercase hexadecimal without separators.
    """

    fingerprint = _require_identifier_text(value, "fingerprint")

    if (
        isinstance(expected_bytes, bool)
        or not isinstance(expected_bytes, int)
        or expected_bytes <= 0
    ):
        raise ValueError("expected_bytes must be a positive integer.")

    if ":" in fingerprint:
        octets = fingerprint.split(":")

        if any(re.fullmatch(r"[0-9a-fA-F]{2}", octet) is None for octet in octets):
            raise ValueError(
                "Colon-separated fingerprints must contain "
                "two hexadecimal characters per byte."
            )

        normalized = "".join(octets).lower()

    else:
        if re.fullmatch(r"[0-9a-fA-F]+", fingerprint) is None:
            raise ValueError("Fingerprint must contain hexadecimal characters.")

        normalized = fingerprint.lower()

    expected_characters = expected_bytes * 2

    if len(normalized) != expected_characters:
        raise ValueError(
            f"Fingerprint must contain exactly {expected_characters} "
            f"hexadecimal characters ({expected_bytes} bytes)."
        )

    return normalized


@dataclass(frozen=True, slots=True)
class _FingerprintProfile:
    """Define the digest algorithm and expected fingerprint length."""

    algorithm: str
    digest_bytes: int


_X509_FINGERPRINT_PROFILES: Mapping[str, _FingerprintProfile] = MappingProxyType(
    {
        X509_FINGERPRINT_SHA1_NAMESPACE: _FingerprintProfile(
            algorithm="sha1",
            digest_bytes=20,
        ),
        X509_FINGERPRINT_SHA256_NAMESPACE: _FingerprintProfile(
            algorithm="sha256",
            digest_bytes=32,
        ),
        X509_FINGERPRINT_SHA384_NAMESPACE: _FingerprintProfile(
            algorithm="sha384",
            digest_bytes=48,
        ),
        X509_FINGERPRINT_SHA512_NAMESPACE: _FingerprintProfile(
            algorithm="sha512",
            digest_bytes=64,
        ),
        X509_FINGERPRINT_SHA3_256_NAMESPACE: _FingerprintProfile(
            algorithm="sha3_256",
            digest_bytes=32,
        ),
        X509_FINGERPRINT_BLAKE2S_256_NAMESPACE: _FingerprintProfile(
            algorithm="blake2s",
            digest_bytes=32,
        ),
        X509_FINGERPRINT_BLAKE2B_512_NAMESPACE: _FingerprintProfile(
            algorithm="blake2b",
            digest_bytes=64,
        ),
        X509_FINGERPRINT_BLAKE3_256_NAMESPACE: _FingerprintProfile(
            algorithm="blake3",
            digest_bytes=32,
        ),
    }
)


def normalize_x509_fingerprint(
    value: str,
    namespace: str,
) -> str:
    """Normalize an X.509 fingerprint using its registered profile."""

    profile = _X509_FINGERPRINT_PROFILES.get(namespace)

    if profile is None:
        raise ValueError(f"Unsupported X.509 fingerprint namespace: {namespace!r}.")

    return normalize_fingerprint(
        value,
        expected_bytes=profile.digest_bytes,
    )


# ---------------------------------------------------------
# Identifier dispatcher
# ---------------------------------------------------------


def normalize_identifier(identifier: AssetIdentifier) -> str:
    """Normalize a supported external identifier for comparison.

    The original AssetIdentifier remains unchanged.
    """

    if not isinstance(identifier, AssetIdentifier):
        raise TypeError("identifier must be an AssetIdentifier.")

    if identifier.namespace == DNS_NAME_NAMESPACE:
        return normalize_dns_name(identifier.value)

    if identifier.namespace == IP_ADDRESS_NAMESPACE:
        return normalize_ip_address(identifier.value)

    if identifier.namespace in _X509_FINGERPRINT_PROFILES:
        return normalize_x509_fingerprint(
            identifier.value,
            identifier.namespace,
        )

    raise ValueError(f"Unsupported identifier namespace: {identifier.namespace!r}.")
