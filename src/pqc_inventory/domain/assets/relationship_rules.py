"""Semantic compatibility rules for asset relationships."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from pqc_inventory.domain.assets.asset import Asset
from pqc_inventory.domain.assets.enums import (
    AssetType,
    RelationshipType,
)
from pqc_inventory.domain.assets.relationships import AssetRelationship


@dataclass(frozen=True, slots=True)
class _RelationshipRule:
    """Define permitted source and target asset classifications."""

    source_types: frozenset[AssetType]
    target_types: frozenset[AssetType]


_ALL_ASSET_TYPES = frozenset(AssetType)


_RELATIONSHIP_RULES: Mapping[
    RelationshipType,
    _RelationshipRule,
] = MappingProxyType(
    {
        RelationshipType.HOSTS: _RelationshipRule(
            source_types=frozenset(
                {
                    AssetType.COMPUTING_SYSTEM,
                }
            ),
            target_types=frozenset(
                {
                    AssetType.APPLICATION,
                    AssetType.SOFTWARE_COMPONENT,
                    AssetType.CRYPTOGRAPHIC_MODULE,
                    AssetType.RANDOMNESS_COMPONENT,
                }
            ),
        ),
        RelationshipType.RUNS: _RelationshipRule(
            source_types=frozenset(
                {
                    AssetType.COMPUTING_SYSTEM,
                    AssetType.APPLICATION,
                }
            ),
            target_types=frozenset(
                {
                    AssetType.SOFTWARE_COMPONENT,
                    AssetType.CRYPTOGRAPHIC_MODULE,
                    AssetType.RANDOMNESS_COMPONENT,
                }
            ),
        ),
        RelationshipType.EXPOSES: _RelationshipRule(
            source_types=frozenset(
                {
                    AssetType.APPLICATION,
                }
            ),
            target_types=frozenset(
                {
                    AssetType.NETWORK_SERVICE,
                }
            ),
        ),
        RelationshipType.PRESENTS: _RelationshipRule(
            source_types=frozenset(
                {
                    AssetType.NETWORK_SERVICE,
                }
            ),
            target_types=frozenset(
                {
                    AssetType.CERTIFICATE,
                }
            ),
        ),
        RelationshipType.USES: _RelationshipRule(
            source_types=frozenset(
                {
                    AssetType.APPLICATION,
                    AssetType.NETWORK_SERVICE,
                    AssetType.SOFTWARE_COMPONENT,
                    AssetType.CRYPTOGRAPHIC_MODULE,
                    AssetType.CRYPTOGRAPHIC_SERVICE,
                }
            ),
            target_types=frozenset(
                {
                    AssetType.SOFTWARE_COMPONENT,
                    AssetType.CERTIFICATE,
                    AssetType.CRYPTOGRAPHIC_KEY_REFERENCE,
                    AssetType.CRYPTOGRAPHIC_MODULE,
                    AssetType.RANDOMNESS_COMPONENT,
                    AssetType.CRYPTOGRAPHIC_SERVICE,
                }
            ),
        ),
        RelationshipType.IMPLEMENTS: _RelationshipRule(
            source_types=frozenset(
                {
                    AssetType.SOFTWARE_COMPONENT,
                    AssetType.CRYPTOGRAPHIC_MODULE,
                }
            ),
            target_types=frozenset(
                {
                    AssetType.CRYPTOGRAPHIC_SERVICE,
                }
            ),
        ),
        RelationshipType.DEPENDS_ON: _RelationshipRule(
            source_types=_ALL_ASSET_TYPES,
            target_types=_ALL_ASSET_TYPES,
        ),
        RelationshipType.MANAGED_BY: _RelationshipRule(
            source_types=_ALL_ASSET_TYPES,
            target_types=frozenset(
                {
                    AssetType.COMPUTING_SYSTEM,
                    AssetType.APPLICATION,
                    AssetType.CRYPTOGRAPHIC_SERVICE,
                }
            ),
        ),
        RelationshipType.CONTAINS: _RelationshipRule(
            source_types=frozenset(
                {
                    AssetType.COMPUTING_SYSTEM,
                    AssetType.APPLICATION,
                    AssetType.SOFTWARE_COMPONENT,
                    AssetType.CERTIFICATE,
                    AssetType.CRYPTOGRAPHIC_MODULE,
                    AssetType.CRYPTOGRAPHIC_SERVICE,
                }
            ),
            target_types=frozenset(
                {
                    AssetType.SOFTWARE_COMPONENT,
                    AssetType.CERTIFICATE,
                    AssetType.CRYPTOGRAPHIC_KEY_REFERENCE,
                    AssetType.CRYPTOGRAPHIC_MODULE,
                    AssetType.RANDOMNESS_COMPONENT,
                }
            ),
        ),
    }
)


def validate_relationship_compatibility(
    relationship: AssetRelationship,
    source_asset: Asset,
    target_asset: Asset,
) -> None:
    """Validate relationship identity and asset classification compatibility.

    Raises:
        TypeError: If the supplied objects have incorrect types.
        ValueError: If the relationship references different assets or
            its source and target classifications are incompatible.
    """

    if not isinstance(relationship, AssetRelationship):
        raise TypeError("relationship must be an AssetRelationship.")

    if not isinstance(source_asset, Asset):
        raise TypeError("source_asset must be an Asset.")

    if not isinstance(target_asset, Asset):
        raise TypeError("target_asset must be an Asset.")

    if relationship.source_asset_id != source_asset.asset_id:
        raise ValueError(
            "source_asset does not match the relationship source_asset_id."
        )

    if relationship.target_asset_id != target_asset.asset_id:
        raise ValueError(
            "target_asset does not match the relationship target_asset_id."
        )

    rule = _RELATIONSHIP_RULES[relationship.relationship_type]

    if source_asset.asset_type not in rule.source_types:
        raise ValueError(
            f"{relationship.relationship_type.value!r} does not permit "
            f"{source_asset.asset_type.value!r} as its source asset."
        )

    if target_asset.asset_type not in rule.target_types:
        raise ValueError(
            f"{relationship.relationship_type.value!r} does not permit "
            f"{target_asset.asset_type.value!r} as its target asset."
        )
