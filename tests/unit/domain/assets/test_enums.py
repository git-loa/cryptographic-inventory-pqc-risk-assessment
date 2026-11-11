"""Tests for asset domain enumerations."""

from pqc_inventory.domain.assets.enums import (
    AssetLifecycleStatus,
    AssetType,
)


def test_asset_types_are_string_enums():
    """Asset types should behave as strings."""

    assert AssetType.NETWORK_SERVICE == "network_service"
    assert isinstance(AssetType.CERTIFICATE, str)


def test_asset_lifecycle_statuses_are_string_enums():
    """Lifecycle statuses should behave as strings."""

    assert isinstance(AssetLifecycleStatus.ACTIVE, str)
    assert isinstance(AssetLifecycleStatus.UNKNOWN, str)

    assert AssetLifecycleStatus.ACTIVE == "active"
    assert AssetLifecycleStatus.UNKNOWN == "unknown"
