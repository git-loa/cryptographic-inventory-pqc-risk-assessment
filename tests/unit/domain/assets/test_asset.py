"""Tests for the cryptographic Asset domain entity."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from pqc_inventory.domain.assets.asset import (
    Asset,
    AssetLifecycle,
)
from pqc_inventory.domain.assets.enums import (
    AssetLifecycleStatus,
    AssetType,
)
from pqc_inventory.domain.assets.identifiers import AssetIdentifier
from pqc_inventory.domain.assets.specifications import (
    CertificateSpecification,
    CryptographicKeyReferenceSpecification,
    NetworkEndpointSpecification,
    SoftwareComponentSpecification,
)


def test_asset_generates_uuid():
    """Generate a unique internal identifier when none is supplied."""

    asset = Asset(
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
    )

    assert isinstance(asset.asset_id, UUID)


def test_asset_accepts_supplied_uuid():
    """Allow an externally supplied internal UUID."""

    asset_id = uuid4()

    asset = Asset(
        asset_id=asset_id,
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
    )

    assert asset.asset_id == asset_id


def test_assets_receive_distinct_identifiers():
    """Different asset instances receive different UUIDs."""

    first = Asset(
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
    )

    second = Asset(
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
    )

    assert first.asset_id != second.asset_id


def test_asset_rejects_invalid_uuid():
    """Require an actual UUID for asset identity."""

    with pytest.raises(TypeError):
        Asset(
            asset_id="invalid",
            asset_type=AssetType.APPLICATION,
            name="Payment Application",
        )


def test_asset_rejects_invalid_asset_type():
    """Require an AssetType enumeration member."""

    with pytest.raises(TypeError):
        Asset(
            asset_type="application",
            name="Payment Application",
        )


@pytest.mark.parametrize("name", ["", "   "])
def test_asset_rejects_empty_name(name):
    """Require a non-empty asset name."""

    with pytest.raises(ValueError):
        Asset(
            asset_type=AssetType.APPLICATION,
            name=name,
        )


def test_asset_rejects_non_string_name():
    """Require the asset name to be a string."""

    with pytest.raises(TypeError):
        Asset(
            asset_type=AssetType.APPLICATION,
            name=123,
        )


def test_asset_allows_optional_description():
    """Allow an asset without a description."""

    asset = Asset(
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
    )

    assert asset.description is None


def test_asset_rejects_empty_description():
    """Reject whitespace-only descriptions."""

    with pytest.raises(ValueError):
        Asset(
            asset_type=AssetType.APPLICATION,
            name="Payment Application",
            description="   ",
        )


def test_asset_accepts_external_identifiers():
    """Associate multiple external identifiers with an asset."""

    identifiers = (
        AssetIdentifier(
            namespace="hostname",
            value="example.com",
        ),
        AssetIdentifier(
            namespace="ip_address",
            value="192.0.2.10",
        ),
    )

    asset = Asset(
        asset_type=AssetType.NETWORK_SERVICE,
        name="Example HTTPS Service",
        identifiers=identifiers,
    )

    assert asset.identifiers == identifiers
    assert len(asset.identifiers) == 2


def test_asset_rejects_list_of_identifiers():
    """Require an immutable tuple of identifiers."""

    with pytest.raises(TypeError):
        Asset(
            asset_type=AssetType.APPLICATION,
            name="Payment Application",
            identifiers=[
                AssetIdentifier(
                    namespace="hostname",
                    value="example.com",
                ),
            ],
        )


def test_asset_rejects_invalid_identifier_objects():
    """Require all identifiers to be AssetIdentifier instances."""

    with pytest.raises(TypeError):
        Asset(
            asset_type=AssetType.APPLICATION,
            name="Payment Application",
            identifiers=("example.com",),
        )


def test_asset_rejects_duplicate_identifiers():
    """Prevent duplicate external identifiers."""

    identifier = AssetIdentifier(
        namespace="hostname",
        value="example.com",
    )

    with pytest.raises(ValueError, match="unique"):
        Asset(
            asset_type=AssetType.NETWORK_SERVICE,
            name="Example Service",
            identifiers=(identifier, identifier),
        )


@pytest.mark.parametrize(
    ("asset_type", "specification"),
    [
        (
            AssetType.NETWORK_SERVICE,
            NetworkEndpointSpecification(
                service_protocol="https",
                port=443,
            ),
        ),
        (
            AssetType.CERTIFICATE,
            CertificateSpecification(
                serial_number="123456789",
            ),
        ),
        (
            AssetType.SOFTWARE_COMPONENT,
            SoftwareComponentSpecification(
                name="OpenSSL",
                version="3.5.5",
            ),
        ),
        (
            AssetType.CRYPTOGRAPHIC_KEY_REFERENCE,
            CryptographicKeyReferenceSpecification(
                algorithm="RSA",
                key_size_bits=2048,
            ),
        ),
    ],
)
def test_asset_accepts_compatible_specification(
    asset_type,
    specification,
):
    """Accept specifications compatible with the asset category."""

    asset = Asset(
        asset_type=asset_type,
        name="Test Asset",
        specification=specification,
    )

    assert asset.specification == specification


def test_asset_allows_missing_specification():
    """Allow asset discovery before technical details are available."""

    asset = Asset(
        asset_type=AssetType.NETWORK_SERVICE,
        name="Discovered HTTPS Service",
    )

    assert asset.specification is None


def test_asset_rejects_incompatible_specification():
    """Reject specifications belonging to another asset category."""

    with pytest.raises(TypeError, match="requires"):
        Asset(
            asset_type=AssetType.CERTIFICATE,
            name="Example Certificate",
            specification=NetworkEndpointSpecification(
                service_protocol="https",
                port=443,
            ),
        )


def test_asset_rejects_specification_for_unsupported_category():
    """Reject specifications without a defined compatibility mapping."""

    with pytest.raises(ValueError, match="No specification type"):
        Asset(
            asset_type=AssetType.APPLICATION,
            name="Payment Application",
            specification=NetworkEndpointSpecification(
                service_protocol="https",
                port=443,
            ),
        )


def test_asset_creates_default_lifecycle():
    """Generate default lifecycle information."""

    asset = Asset(
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
    )

    assert asset.lifecycle_status is AssetLifecycleStatus.UNKNOWN
    assert isinstance(asset.created_at, datetime)
    assert isinstance(asset.updated_at, datetime)

    assert asset.created_at.tzinfo is not None
    assert asset.updated_at.tzinfo is not None

    assert asset.updated_at >= asset.created_at


def test_asset_accepts_supplied_lifecycle():
    """Allow an explicitly supplied lifecycle object."""

    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    lifecycle = AssetLifecycle(
        status=AssetLifecycleStatus.ACTIVE,
        created_at=timestamp,
        updated_at=timestamp,
    )

    asset = Asset(
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
        lifecycle=lifecycle,
    )

    assert asset.lifecycle is lifecycle
    assert asset.lifecycle_status is AssetLifecycleStatus.ACTIVE


def test_asset_rejects_invalid_lifecycle():
    """Require an AssetLifecycle instance."""

    with pytest.raises(TypeError):
        Asset(
            asset_type=AssetType.APPLICATION,
            name="Payment Application",
            lifecycle="active",
        )


def test_asset_is_immutable():
    """Prevent direct modification of asset attributes."""

    asset = Asset(
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
    )

    with pytest.raises(FrozenInstanceError):
        asset.name = "Another Application"


def test_asset_lifecycle_status_property():
    """Expose lifecycle status through the asset entity."""

    asset = Asset(
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
    )

    assert asset.lifecycle_status is AssetLifecycleStatus.UNKNOWN


def test_asset_lifecycle_update_preserves_identity():
    """Preserve asset identity when lifecycle status changes."""

    asset = Asset(
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
    )

    updated_asset = asset.with_lifecycle_status(
        AssetLifecycleStatus.ACTIVE,
    )

    assert updated_asset.asset_id == asset.asset_id
    assert updated_asset.lifecycle_status is AssetLifecycleStatus.ACTIVE


def test_asset_lifecycle_update_preserves_creation_timestamp():
    """Preserve the original creation timestamp."""

    asset = Asset(
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
    )

    updated_asset = asset.with_lifecycle_status(
        AssetLifecycleStatus.ACTIVE,
    )

    assert updated_asset.created_at == asset.created_at


def test_asset_lifecycle_update_uses_supplied_timestamp():
    """Allow a deterministic timestamp for lifecycle updates."""

    created = datetime(2026, 1, 1, tzinfo=timezone.utc)
    updated = datetime(2026, 2, 1, tzinfo=timezone.utc)

    lifecycle = AssetLifecycle(
        created_at=created,
        updated_at=created,
    )

    asset = Asset(
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
        lifecycle=lifecycle,
    )

    updated_asset = asset.with_lifecycle_status(
        AssetLifecycleStatus.INACTIVE,
        updated_at=updated,
    )

    assert updated_asset.updated_at == updated
    assert updated_asset.created_at == created


def test_asset_lifecycle_update_does_not_modify_original():
    """Preserve the original asset during lifecycle changes."""

    asset = Asset(
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
    )

    updated_asset = asset.with_lifecycle_status(
        AssetLifecycleStatus.ACTIVE,
    )

    assert asset.lifecycle_status is AssetLifecycleStatus.UNKNOWN
    assert updated_asset.lifecycle_status is AssetLifecycleStatus.ACTIVE


def test_same_lifecycle_status_returns_original_asset():
    """Avoid creating a new version when the status is unchanged."""

    asset = Asset(
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
    )

    result = asset.with_lifecycle_status(
        AssetLifecycleStatus.UNKNOWN,
    )

    assert result is asset


def test_asset_lifecycle_update_rejects_invalid_status():
    """Require a valid lifecycle status."""

    asset = Asset(
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
    )

    with pytest.raises(TypeError):
        asset.with_lifecycle_status("active")


def test_asset_lifecycle_update_rejects_earlier_timestamp():
    """Prevent lifecycle timestamps from moving backwards."""

    created = datetime(2026, 2, 1, tzinfo=timezone.utc)
    earlier = created - timedelta(days=1)

    asset = Asset(
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
        lifecycle=AssetLifecycle(
            created_at=created,
            updated_at=created,
        ),
    )

    with pytest.raises(ValueError):
        asset.with_lifecycle_status(
            AssetLifecycleStatus.ACTIVE,
            updated_at=earlier,
        )


def test_asset_lifecycle_update_rejects_timestamp_before_previous_update():
    """Prevent lifecycle update timestamps from moving backwards."""

    created = datetime(2026, 1, 1, tzinfo=timezone.utc)
    previous_update = datetime(2026, 2, 1, tzinfo=timezone.utc)
    earlier_update = datetime(2026, 1, 15, tzinfo=timezone.utc)

    asset = Asset(
        asset_type=AssetType.APPLICATION,
        name="Payment Application",
        lifecycle=AssetLifecycle(
            status=AssetLifecycleStatus.ACTIVE,
            created_at=created,
            updated_at=previous_update,
        ),
    )

    with pytest.raises(
        ValueError,
        match="previous update timestamp",
    ):
        asset.with_lifecycle_status(
            AssetLifecycleStatus.INACTIVE,
            updated_at=earlier_update,
        )
