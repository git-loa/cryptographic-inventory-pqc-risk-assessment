"""Tests for asset relationship compatibility rules."""

import pytest

from pqc_inventory.domain.assets.asset import Asset
from pqc_inventory.domain.assets.enums import (
    AssetType,
    RelationshipType,
)
from pqc_inventory.domain.assets.relationship_rules import (
    _RELATIONSHIP_RULES,
    _RelationshipRule,
    validate_relationship_compatibility,
)
from pqc_inventory.domain.assets.relationships import AssetRelationship


def _create_asset(asset_type: AssetType) -> Asset:
    """Create an asset for relationship testing."""

    return Asset(
        asset_type=asset_type,
        name=f"Test {asset_type.value}",
    )


def _create_relationship(
    source: Asset,
    target: Asset,
    relationship_type: RelationshipType,
) -> AssetRelationship:
    """Create a relationship between two test assets."""

    return AssetRelationship(
        source_asset_id=source.asset_id,
        target_asset_id=target.asset_id,
        relationship_type=relationship_type,
    )


def test_relationship_rules_cover_all_relationship_types():
    """Define a compatibility rule for every relationship type."""

    assert set(_RELATIONSHIP_RULES) == set(RelationshipType)


def test_relationship_rules_use_immutable_values():
    """Store relationship compatibility definitions immutably."""

    for rule in _RELATIONSHIP_RULES.values():
        assert isinstance(rule, _RelationshipRule)
        assert isinstance(rule.source_types, frozenset)
        assert isinstance(rule.target_types, frozenset)


def test_relationship_rules_mapping_is_immutable():
    """Prevent modification of the compatibility mapping."""

    with pytest.raises(TypeError):
        _RELATIONSHIP_RULES[RelationshipType.USES] = _RELATIONSHIP_RULES[
            RelationshipType.HOSTS
        ]


@pytest.mark.parametrize(
    ("source_type", "target_type", "relationship_type"),
    [
        (
            AssetType.COMPUTING_SYSTEM,
            AssetType.APPLICATION,
            RelationshipType.HOSTS,
        ),
        (
            AssetType.COMPUTING_SYSTEM,
            AssetType.NETWORK_SERVICE,
            RelationshipType.HOSTS,
        ),
        (
            AssetType.COMPUTING_SYSTEM,
            AssetType.APPLICATION,
            RelationshipType.RUNS,
        ),
        (
            AssetType.APPLICATION,
            AssetType.NETWORK_SERVICE,
            RelationshipType.EXPOSES,
        ),
        (
            AssetType.NETWORK_SERVICE,
            AssetType.CERTIFICATE,
            RelationshipType.PRESENTS,
        ),
        (
            AssetType.APPLICATION,
            AssetType.SOFTWARE_COMPONENT,
            RelationshipType.USES,
        ),
        (
            AssetType.SOFTWARE_COMPONENT,
            AssetType.CRYPTOGRAPHIC_SERVICE,
            RelationshipType.PROVIDES,
        ),
        (
            AssetType.CRYPTOGRAPHIC_MODULE,
            AssetType.RANDOMNESS_COMPONENT,
            RelationshipType.DEPENDS_ON,
        ),
        (
            AssetType.CRYPTOGRAPHIC_KEY_REFERENCE,
            AssetType.CRYPTOGRAPHIC_SERVICE,
            RelationshipType.MANAGED_BY,
        ),
        (
            AssetType.CERTIFICATE,
            AssetType.CRYPTOGRAPHIC_KEY_REFERENCE,
            RelationshipType.CONTAINS,
        ),
    ],
)
def test_valid_relationship_combinations_are_accepted(
    source_type,
    target_type,
    relationship_type,
):
    """Accept relationships with permitted asset classifications."""

    source = _create_asset(source_type)
    target = _create_asset(target_type)

    relationship = _create_relationship(
        source,
        target,
        relationship_type,
    )

    validate_relationship_compatibility(
        relationship,
        source,
        target,
    )


@pytest.mark.parametrize(
    ("source_type", "target_type", "relationship_type"),
    [
        (
            AssetType.CERTIFICATE,
            AssetType.COMPUTING_SYSTEM,
            RelationshipType.HOSTS,
        ),
        (
            AssetType.APPLICATION,
            AssetType.SOFTWARE_COMPONENT,
            RelationshipType.RUNS,
        ),
        (
            AssetType.NETWORK_SERVICE,
            AssetType.APPLICATION,
            RelationshipType.EXPOSES,
        ),
        (
            AssetType.CERTIFICATE,
            AssetType.NETWORK_SERVICE,
            RelationshipType.PRESENTS,
        ),
        (
            AssetType.APPLICATION,
            AssetType.CRYPTOGRAPHIC_SERVICE,
            RelationshipType.PROVIDES,
        ),
        (
            AssetType.RANDOMNESS_COMPONENT,
            AssetType.NETWORK_SERVICE,
            RelationshipType.MANAGED_BY,
        ),
        (
            AssetType.CRYPTOGRAPHIC_KEY_REFERENCE,
            AssetType.COMPUTING_SYSTEM,
            RelationshipType.CONTAINS,
        ),
    ],
)
def test_invalid_relationship_combinations_are_rejected(
    source_type,
    target_type,
    relationship_type,
):
    """Reject relationships with incompatible asset classifications."""

    source = _create_asset(source_type)
    target = _create_asset(target_type)

    relationship = _create_relationship(
        source,
        target,
        relationship_type,
    )

    with pytest.raises(ValueError):
        validate_relationship_compatibility(
            relationship,
            source,
            target,
        )


def test_dependency_relationship_allows_all_asset_categories():
    """Allow dependencies between different asset categories."""

    for source_type in AssetType:
        for target_type in AssetType:
            if source_type is target_type:
                continue

            source = _create_asset(source_type)
            target = _create_asset(target_type)

            relationship = _create_relationship(
                source,
                target,
                RelationshipType.DEPENDS_ON,
            )

            validate_relationship_compatibility(
                relationship,
                source,
                target,
            )


def test_relationship_rejects_incorrect_source_asset():
    """Reject a source asset that does not match the relationship."""

    source = _create_asset(AssetType.APPLICATION)
    target = _create_asset(AssetType.NETWORK_SERVICE)
    unrelated = _create_asset(AssetType.COMPUTING_SYSTEM)

    relationship = _create_relationship(
        source,
        target,
        RelationshipType.EXPOSES,
    )

    with pytest.raises(ValueError, match="source_asset"):
        validate_relationship_compatibility(
            relationship,
            unrelated,
            target,
        )


def test_relationship_rejects_incorrect_target_asset():
    """Reject a target asset that does not match the relationship."""

    source = _create_asset(AssetType.APPLICATION)
    target = _create_asset(AssetType.NETWORK_SERVICE)
    unrelated = _create_asset(AssetType.CERTIFICATE)

    relationship = _create_relationship(
        source,
        target,
        RelationshipType.EXPOSES,
    )

    with pytest.raises(ValueError, match="target_asset"):
        validate_relationship_compatibility(
            relationship,
            source,
            unrelated,
        )


@pytest.mark.parametrize(
    ("relationship", "source", "target"),
    [
        ("invalid", Asset, Asset),
        (AssetRelationship, "invalid", Asset),
        (AssetRelationship, Asset, "invalid"),
    ],
)
def test_relationship_validator_rejects_invalid_objects(
    relationship,
    source,
    target,
):
    """Reject objects that do not satisfy the validator contract."""

    with pytest.raises(TypeError):
        validate_relationship_compatibility(
            relationship,
            source,
            target,
        )


def test_relationship_validator_enforces_all_declared_rules():
    """Enforce all declared source and target compatibility rules."""

    for relationship_type, rule in _RELATIONSHIP_RULES.items():
        for source_type in AssetType:
            for target_type in AssetType:
                source = _create_asset(source_type)
                target = _create_asset(target_type)

                relationship = _create_relationship(
                    source,
                    target,
                    relationship_type,
                )

                is_compatible = (
                    source_type in rule.source_types
                    and target_type in rule.target_types
                )

                if is_compatible:
                    validate_relationship_compatibility(
                        relationship,
                        source,
                        target,
                    )
                else:
                    with pytest.raises(ValueError):
                        validate_relationship_compatibility(
                            relationship,
                            source,
                            target,
                        )
