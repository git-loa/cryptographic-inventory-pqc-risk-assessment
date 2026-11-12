"""Core cryptographic asset domain entity."""

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pqc_inventory.domain.assets._validation import (
    validate_aware_datetime,
    validate_datetime_interval,
    validate_optional_text,
    validate_required_text,
    validate_uuid,
)
from pqc_inventory.domain.assets.enums import (
    AssetLifecycleStatus,
    AssetType,
)
from pqc_inventory.domain.assets.identifiers import AssetIdentifier
from pqc_inventory.domain.assets.specifications import (
    AssetSpecification,
    CertificateSpecification,
    CryptographicKeyReferenceSpecification,
    NetworkEndpointSpecification,
    SoftwareComponentSpecification,
)


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class AssetLifecycle:
    """Represent the lifecycle state and timestamps of an asset."""

    status: AssetLifecycleStatus = AssetLifecycleStatus.UNKNOWN
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        """Validate asset lifecycle information."""

        if not isinstance(self.status, AssetLifecycleStatus):
            raise TypeError("status must be an AssetLifecycleStatus.")

        validate_datetime_interval(
            self.created_at,
            self.updated_at,
            "created_at",
            "updated_at",
        )


# Maps currently supported asset specifications to their asset categories.
_SPECIFICATION_TYPES = {
    AssetType.NETWORK_SERVICE: NetworkEndpointSpecification,
    AssetType.CERTIFICATE: CertificateSpecification,
    AssetType.SOFTWARE_COMPONENT: SoftwareComponentSpecification,
    AssetType.CRYPTOGRAPHIC_KEY_REFERENCE: CryptographicKeyReferenceSpecification,
}


@dataclass(frozen=True, slots=True)
class Asset:
    """Represent an identifiable computing or cryptographic asset."""

    asset_type: AssetType
    name: str
    asset_id: UUID = field(default_factory=uuid4)
    description: str | None = None
    identifiers: tuple[AssetIdentifier, ...] = ()
    specification: AssetSpecification | None = None
    lifecycle: AssetLifecycle = field(default_factory=AssetLifecycle)

    def __post_init__(self) -> None:
        """Validate asset identity, classification and composition."""

        self._validate_identity()
        self._validate_classification()
        self._validate_identifiers()
        self._validate_specification()
        self._validate_lifecycle()

    def _validate_identity(self) -> None:
        """Validate asset identity and descriptive attributes."""

        validate_uuid(self.asset_id, "asset_id")
        validate_required_text(self.name, "name")
        validate_optional_text(self.description, "description")

    def _validate_classification(self) -> None:
        """Require a recognized asset classification."""

        if not isinstance(self.asset_type, AssetType):
            raise TypeError("asset_type must be an AssetType.")

    def _validate_identifiers(self) -> None:
        """Validate external identifiers and prevent duplicates."""

        if not isinstance(self.identifiers, tuple):
            raise TypeError("identifiers must be a tuple of AssetIdentifier.")

        if not all(
            isinstance(identifier, AssetIdentifier) for identifier in self.identifiers
        ):
            raise TypeError("All identifiers must be AssetIdentifier instances.")

        if len(set(self.identifiers)) != len(self.identifiers):
            raise ValueError("Asset identifiers must be unique.")

    def _validate_specification(self) -> None:
        """Validate specification compatibility with the asset type."""

        if self.specification is None:
            return

        expected_type = _SPECIFICATION_TYPES.get(self.asset_type)

        if expected_type is None:
            raise ValueError(
                f"No specification type is currently defined for "
                f"asset type {self.asset_type.value!r}."
            )

        if not isinstance(self.specification, expected_type):
            raise TypeError(
                f"{self.asset_type.value} requires "
                f"{expected_type.__name__}, not "
                f"{type(self.specification).__name__}."
            )

    def _validate_lifecycle(self) -> None:
        """Validate the asset lifecycle object."""

        if not isinstance(self.lifecycle, AssetLifecycle):
            raise TypeError("lifecycle must be an AssetLifecycle.")

    @property
    def lifecycle_status(self) -> AssetLifecycleStatus:
        """Return the current lifecycle status."""

        return self.lifecycle.status

    @property
    def created_at(self) -> datetime:
        """Return the asset creation timestamp."""

        return self.lifecycle.created_at

    @property
    def updated_at(self) -> datetime:
        """Return the asset update timestamp."""

        return self.lifecycle.updated_at

    def with_lifecycle_status(
        self,
        status: AssetLifecycleStatus,
        *,
        updated_at: datetime | None = None,
    ) -> "Asset":
        """Return a new asset with an updated lifecycle status.

        The internal asset identity and creation timestamp remain unchanged.
        Lifecycle timestamps cannot move backwards.
        """

        if not isinstance(status, AssetLifecycleStatus):
            raise TypeError("status must be an AssetLifecycleStatus.")

        if status == self.lifecycle.status:
            return self

        timestamp = updated_at if updated_at is not None else _utc_now()

        validate_aware_datetime(timestamp, "updated_at")

        if timestamp < self.lifecycle.updated_at:
            raise ValueError(
                "updated_at cannot be earlier than the previous update timestamp."
            )

        updated_lifecycle = replace(
            self.lifecycle,
            status=status,
            updated_at=timestamp,
        )

        return replace(
            self,
            lifecycle=updated_lifecycle,
        )
