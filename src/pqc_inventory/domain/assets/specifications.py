"""Typed specifications for cryptographic assets."""

from dataclasses import dataclass
from datetime import datetime
from typing import TypeAlias

from pqc_inventory.domain.assets._validation import (
    validate_aware_datetime,
    validate_optional_text,
    validate_positive_integer,
    validate_required_text,
)


@dataclass(frozen=True, slots=True)
class NetworkEndpointSpecification:
    """Describe the technical properties of a network endpoint."""

    service_protocol: str
    port: int
    transport_protocol: str = "tcp"

    def __post_init__(self) -> None:
        """Validate network endpoint properties."""

        validate_required_text(self.service_protocol, "service_protocol")
        validate_required_text(self.transport_protocol, "transport_protocol")

        if (
            isinstance(self.port, bool)
            or not isinstance(self.port, int)
            or not 1 <= self.port <= 65535
        ):
            raise ValueError("port must be an integer between 1 and 65535.")


@dataclass(frozen=True, slots=True)
class CertificateValidity:
    """Represent the validity period of an X.509 certificate."""

    not_before: datetime | None = None
    not_after: datetime | None = None

    def __post_init__(self) -> None:
        """Validate certificate validity dates."""

        validate_aware_datetime(self.not_before, "not_before")
        validate_aware_datetime(self.not_after, "not_after")

        if (
            self.not_before is not None
            and self.not_after is not None
            and self.not_before > self.not_after
        ):
            raise ValueError("not_before cannot be later than not_after.")


@dataclass(frozen=True, slots=True)
class PublicKeyInfo:
    """Describe the public-key characteristics of a certificate."""

    algorithm: str
    key_size_bits: int | None = None
    curve: str | None = None

    def __post_init__(self) -> None:
        """Validate public-key metadata."""

        validate_required_text(self.algorithm, "algorithm")

        validate_positive_integer(
            self.key_size_bits,
            "key_size_bits",
        )

        validate_optional_text(self.curve, "curve")


@dataclass(frozen=True, slots=True)
class CertificateSpecification:
    """Describe metadata associated with an X.509 certificate."""

    serial_number: str
    subject: str | None = None
    issuer: str | None = None
    validity: CertificateValidity | None = None
    signature_algorithm: str | None = None
    public_key: PublicKeyInfo | None = None

    def __post_init__(self) -> None:
        """Validate certificate metadata."""

        validate_required_text(self.serial_number, "serial_number")
        validate_optional_text(self.subject, "subject")
        validate_optional_text(self.issuer, "issuer")
        validate_optional_text(
            self.signature_algorithm,
            "signature_algorithm",
        )

        if self.validity is not None and not isinstance(
            self.validity, CertificateValidity
        ):
            raise TypeError("validity must be a CertificateValidity.")

        if self.public_key is not None and not isinstance(
            self.public_key, PublicKeyInfo
        ):
            raise TypeError("public_key must be a PublicKeyInfo.")


@dataclass(frozen=True, slots=True)
class SoftwareComponentSpecification:
    """Describe an installed or referenced software component."""

    name: str
    version: str | None = None
    vendor: str | None = None
    ecosystem: str | None = None

    def __post_init__(self) -> None:
        """Validate software component metadata."""

        validate_required_text(self.name, "name")
        validate_optional_text(self.version, "version")
        validate_optional_text(self.vendor, "vendor")
        validate_optional_text(self.ecosystem, "ecosystem")


@dataclass(frozen=True, slots=True)
class CryptographicKeySpecification:
    """Describe cryptographic key metadata without storing key material."""

    algorithm: str
    key_size_bits: int | None = None
    curve: str | None = None
    key_usage: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate cryptographic key metadata."""

        validate_required_text(self.algorithm, "algorithm")

        validate_positive_integer(
            self.key_size_bits,
            "key_size_bits",
        )

        validate_optional_text(self.curve, "curve")

        if not isinstance(self.key_usage, tuple):
            raise TypeError("key_usage must be a tuple of strings.")

        for usage in self.key_usage:
            validate_required_text(usage, "key_usage entry")


AssetSpecification: TypeAlias = (
    NetworkEndpointSpecification
    | CertificateSpecification
    | SoftwareComponentSpecification
    | CryptographicKeySpecification
)
