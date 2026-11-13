"""Tests for asset domain enumerations."""

from pqc_inventory.domain.assets.enums import (
    AssetLifecycleStatus,
    AssetType,
    RelationshipType,
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


def test_relationship_types_are_string_enums():
    """Verify relationship types and their string values."""

    expected = {
        "HOSTS",
        "RUNS",
        "EXPOSES",
        "PRESENTS",
        "USES",
        "PROVIDES",
        "DEPENDS_ON",
        "MANAGED_BY",
        "CONTAINS",
    }

    assert {item.name for item in RelationshipType} == expected

    assert all(isinstance(item, str) for item in RelationshipType)
