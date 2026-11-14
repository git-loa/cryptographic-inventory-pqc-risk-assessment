"""Normalize external asset identifiers for identity comparison."""

import ipaddress
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

import idna

from pqc_inventory.domain.assets.identifiers import AssetIdentifier

# ---------------------------------------------------------
# Identifier namespaces
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Shared validation
# ---------------------------------------------------------


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
# DNS and IP normalization
# ---------------------------------------------------------


def normalize_dns_name(value: str) -> str:
    """Return the canonical ASCII representation of a DNS name."""

    hostname = _require_identifier_text(value, "DNS name")

    if any(character.isspace() for character in hostname):
        raise ValueError("DNS name cannot contain whitespace.")

    # Remove the optional trailing DNS root dot.
    hostname = hostname.removesuffix(".")

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


_HEX_PATTERN = re.compile(r"[0-9a-fA-F]+")
_HEX_BYTE_PATTERN = re.compile(r"[0-9a-fA-F]{2}")


def normalize_fingerprint(
    value: str,
    *,
    expected_bytes: int,
) -> str:
    """Normalize a hexadecimal fingerprint.

    Accepts contiguous hexadecimal characters or colon-separated bytes.

    Returns lowercase hexadecimal without separators.
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

        if any(_HEX_BYTE_PATTERN.fullmatch(octet) is None for octet in octets):
            raise ValueError(
                "Colon-separated fingerprints must contain "
                "two hexadecimal characters per byte."
            )

        normalized = "".join(octets).lower()

    else:
        if _HEX_PATTERN.fullmatch(fingerprint) is None:
            raise ValueError("Fingerprint must contain hexadecimal characters.")

        normalized = fingerprint.lower()

    expected_characters = expected_bytes * 2

    if len(normalized) != expected_characters:
        raise ValueError(
            f"Fingerprint must contain exactly {expected_characters} "
            f"hexadecimal characters ({expected_bytes} bytes)."
        )

    return normalized


# ---------------------------------------------------------
# X.509 fingerprint profiles
# ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _FingerprintProfile:
    """Define the length and legacy classification of a fingerprint."""

    digest_bytes: int
    legacy: bool = False


_X509_FINGERPRINT_PROFILES: Mapping[str, _FingerprintProfile] = MappingProxyType(
    {
        X509_FINGERPRINT_SHA1_NAMESPACE: _FingerprintProfile(
            digest_bytes=20,
            legacy=True,
        ),
        X509_FINGERPRINT_SHA256_NAMESPACE: _FingerprintProfile(
            digest_bytes=32,
        ),
        X509_FINGERPRINT_SHA384_NAMESPACE: _FingerprintProfile(
            digest_bytes=48,
        ),
        X509_FINGERPRINT_SHA512_NAMESPACE: _FingerprintProfile(
            digest_bytes=64,
        ),
        X509_FINGERPRINT_SHA3_256_NAMESPACE: _FingerprintProfile(
            digest_bytes=32,
        ),
        X509_FINGERPRINT_BLAKE2S_256_NAMESPACE: _FingerprintProfile(
            digest_bytes=32,
        ),
        X509_FINGERPRINT_BLAKE2B_512_NAMESPACE: _FingerprintProfile(
            digest_bytes=64,
        ),
        X509_FINGERPRINT_BLAKE3_256_NAMESPACE: _FingerprintProfile(
            digest_bytes=32,
        ),
    }
)


# Derived from the profile registry to avoid maintaining duplicate lists.

X509_FINGERPRINT_NAMESPACES = frozenset(_X509_FINGERPRINT_PROFILES)

X509_FINGERPRINT_LEGACY_NAMESPACES = frozenset(
    namespace
    for namespace, profile in _X509_FINGERPRINT_PROFILES.items()
    if profile.legacy
)


def normalize_x509_fingerprint(
    value: str,
    namespace: str,
) -> str:
    """Normalize an X.509 fingerprint using its registered profile."""

    fingerprint_namespace = _require_identifier_text(
        namespace,
        "fingerprint namespace",
    )

    profile = _X509_FINGERPRINT_PROFILES.get(fingerprint_namespace)

    if profile is None:
        raise ValueError(
            f"Unsupported X.509 fingerprint namespace: " f"{fingerprint_namespace!r}."
        )

    return normalize_fingerprint(
        value,
        expected_bytes=profile.digest_bytes,
    )


# ---------------------------------------------------------
# Identifier dispatch
# ---------------------------------------------------------


IdentifierNormalizer = Callable[[str], str]


_IDENTIFIER_NORMALIZERS: Mapping[str, IdentifierNormalizer] = MappingProxyType(
    {
        DNS_NAME_NAMESPACE: normalize_dns_name,
        IP_ADDRESS_NAMESPACE: normalize_ip_address,
    }
)


def normalize_identifier(identifier: AssetIdentifier) -> str:
    """Normalize a supported external identifier for comparison.

    The original AssetIdentifier remains unchanged.
    """

    if not isinstance(identifier, AssetIdentifier):
        raise TypeError("identifier must be an AssetIdentifier.")

    normalizer = _IDENTIFIER_NORMALIZERS.get(identifier.namespace)

    if normalizer is not None:
        return normalizer(identifier.value)

    if identifier.namespace in X509_FINGERPRINT_NAMESPACES:
        return normalize_x509_fingerprint(
            identifier.value,
            identifier.namespace,
        )

    raise ValueError(f"Unsupported identifier namespace: {identifier.namespace!r}.")
