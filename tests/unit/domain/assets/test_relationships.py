"""Tests for asset relationships."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from pqc_inventory.domain.assets.enums import RelationshipType
from pqc_inventory.domain.assets.relationships import AssetRelationship


def test_create_asset_relationship():
    """Create a valid directed asset relationship."""

    source_id = uuid4()
    target_id = uuid4()

    relationship = AssetRelationship(
        source_asset_id=source_id,
        target_asset_id=target_id,
        relationship_type=RelationshipType.USES,
    )

    assert isinstance(relationship.relationship_id, UUID)
    assert relationship.source_asset_id == source_id
    assert relationship.target_asset_id == target_id
    assert relationship.relationship_type is RelationshipType.USES


def test_relationship_generates_unique_uuid():
    """Generate a distinct UUID for each relationship."""

    source_id = uuid4()
    target_id = uuid4()

    first = AssetRelationship(
        source_asset_id=source_id,
        target_asset_id=target_id,
        relationship_type=RelationshipType.USES,
    )

    second = AssetRelationship(
        source_asset_id=source_id,
        target_asset_id=target_id,
        relationship_type=RelationshipType.DEPENDS_ON,
    )

    assert first.relationship_id != second.relationship_id


def test_relationship_accepts_supplied_uuid():
    """Allow an explicitly supplied relationship UUID."""

    relationship_id = uuid4()

    relationship = AssetRelationship(
        relationship_id=relationship_id,
        source_asset_id=uuid4(),
        target_asset_id=uuid4(),
        relationship_type=RelationshipType.HOSTS,
    )

    assert relationship.relationship_id == relationship_id


@pytest.mark.parametrize(
    "field_name",
    [
        "relationship_id",
        "source_asset_id",
        "target_asset_id",
    ],
)
def test_relationship_rejects_invalid_uuid(field_name):
    """Require UUID values for relationship identifiers."""

    attributes = {
        "source_asset_id": uuid4(),
        "target_asset_id": uuid4(),
        "relationship_type": RelationshipType.USES,
    }

    attributes[field_name] = "invalid"

    with pytest.raises(TypeError, match="UUID"):
        AssetRelationship(**attributes)


def test_relationship_rejects_self_reference():
    """Reject relationships whose source and target are identical."""

    asset_id = uuid4()

    with pytest.raises(ValueError, match="different"):
        AssetRelationship(
            source_asset_id=asset_id,
            target_asset_id=asset_id,
            relationship_type=RelationshipType.USES,
        )


def test_relationship_rejects_invalid_relationship_type():
    """Require a RelationshipType enumeration member."""

    with pytest.raises(TypeError, match="RelationshipType"):
        AssetRelationship(
            source_asset_id=uuid4(),
            target_asset_id=uuid4(),
            relationship_type="uses",
        )


def test_relationship_accepts_evidence_references():
    """Associate multiple supporting evidence identifiers."""

    evidence_ids = (uuid4(), uuid4())

    relationship = AssetRelationship(
        source_asset_id=uuid4(),
        target_asset_id=uuid4(),
        relationship_type=RelationshipType.USES,
        evidence_references=evidence_ids,
    )

    assert relationship.evidence_references == evidence_ids


def test_relationship_allows_no_evidence_references():
    """Allow relationships without supporting evidence yet."""

    relationship = AssetRelationship(
        source_asset_id=uuid4(),
        target_asset_id=uuid4(),
        relationship_type=RelationshipType.HOSTS,
    )

    assert not relationship.evidence_references


def test_relationship_rejects_list_of_evidence_references():
    """Require immutable evidence reference collections."""

    with pytest.raises(TypeError, match="tuple"):
        AssetRelationship(
            source_asset_id=uuid4(),
            target_asset_id=uuid4(),
            relationship_type=RelationshipType.USES,
            evidence_references=[uuid4()],
        )


def test_relationship_rejects_invalid_evidence_reference():
    """Require every evidence reference to be a UUID."""

    with pytest.raises(TypeError, match="UUID"):
        AssetRelationship(
            source_asset_id=uuid4(),
            target_asset_id=uuid4(),
            relationship_type=RelationshipType.USES,
            evidence_references=(uuid4(), "invalid"),
        )


def test_relationship_rejects_duplicate_evidence_references():
    """Prevent duplicate supporting evidence identifiers."""

    evidence_id = uuid4()

    with pytest.raises(ValueError, match="unique"):
        AssetRelationship(
            source_asset_id=uuid4(),
            target_asset_id=uuid4(),
            relationship_type=RelationshipType.USES,
            evidence_references=(evidence_id, evidence_id),
        )


def test_relationship_accepts_validity_period():
    """Accept a valid relationship validity period."""

    valid_from = datetime(2026, 1, 1, tzinfo=timezone.utc)
    valid_until = datetime(2026, 12, 31, tzinfo=timezone.utc)

    relationship = AssetRelationship(
        source_asset_id=uuid4(),
        target_asset_id=uuid4(),
        relationship_type=RelationshipType.USES,
        valid_from=valid_from,
        valid_until=valid_until,
    )

    assert relationship.valid_from == valid_from
    assert relationship.valid_until == valid_until


def test_relationship_allows_open_ended_validity():
    """Allow relationships without a known end date."""

    valid_from = datetime(2026, 1, 1, tzinfo=timezone.utc)

    relationship = AssetRelationship(
        source_asset_id=uuid4(),
        target_asset_id=uuid4(),
        relationship_type=RelationshipType.USES,
        valid_from=valid_from,
    )

    assert relationship.valid_from == valid_from
    assert relationship.valid_until is None


def test_relationship_allows_unknown_validity():
    """Allow relationships with unknown validity timestamps."""

    relationship = AssetRelationship(
        source_asset_id=uuid4(),
        target_asset_id=uuid4(),
        relationship_type=RelationshipType.USES,
    )

    assert relationship.valid_from is None
    assert relationship.valid_until is None


@pytest.mark.parametrize(
    "field_name",
    ["valid_from", "valid_until"],
)
def test_relationship_rejects_naive_datetime(field_name):
    """Require relationship validity timestamps to be timezone-aware."""

    with pytest.raises(ValueError, match="timezone-aware"):
        AssetRelationship(
            source_asset_id=uuid4(),
            target_asset_id=uuid4(),
            relationship_type=RelationshipType.USES,
            **{field_name: datetime(2026, 1, 1)},
        )


@pytest.mark.parametrize(
    "field_name",
    ["valid_from", "valid_until"],
)
def test_relationship_rejects_invalid_datetime_type(field_name):
    """Require datetime values for relationship validity."""

    with pytest.raises(TypeError, match="datetime"):
        AssetRelationship(
            source_asset_id=uuid4(),
            target_asset_id=uuid4(),
            relationship_type=RelationshipType.USES,
            **{field_name: "2026-01-01"},
        )


def test_relationship_rejects_reversed_validity_period():
    """Reject validity periods whose end precedes their start."""

    valid_from = datetime(2026, 12, 31, tzinfo=timezone.utc)
    valid_until = datetime(2026, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="valid_from"):
        AssetRelationship(
            source_asset_id=uuid4(),
            target_asset_id=uuid4(),
            relationship_type=RelationshipType.USES,
            valid_from=valid_from,
            valid_until=valid_until,
        )


def test_relationship_is_immutable():
    """Prevent modification of relationship attributes."""

    relationship = AssetRelationship(
        source_asset_id=uuid4(),
        target_asset_id=uuid4(),
        relationship_type=RelationshipType.USES,
    )

    with pytest.raises(FrozenInstanceError):
        relationship.relationship_type = RelationshipType.HOSTS
