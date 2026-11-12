"""Directed relationships between cryptographic assets."""

# pylint: disable=duplicate-code
# Both AssetIdentifier and AssetRelationship legitimately use the same
# datetime interval validation for their respective validity periods.

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from pqc_inventory.domain.assets._validation import (
    validate_datetime_interval,
    validate_uuid,
)
from pqc_inventory.domain.assets.enums import RelationshipType


@dataclass(frozen=True, slots=True)
class AssetRelationship:
    """Represent a directed relationship between two assets."""

    source_asset_id: UUID
    target_asset_id: UUID
    relationship_type: RelationshipType

    relationship_id: UUID = field(default_factory=uuid4)

    valid_from: datetime | None = None
    valid_until: datetime | None = None

    evidence_references: tuple[UUID, ...] = ()

    def __post_init__(self) -> None:
        """Validate relationship identity, references and validity."""

        self._validate_identity()
        self._validate_relationship_type()
        self._validate_evidence_references()
        self._validate_validity()

    def _validate_identity(self) -> None:
        """Validate relationship and asset identifiers."""

        validate_uuid(self.relationship_id, "relationship_id")
        validate_uuid(self.source_asset_id, "source_asset_id")
        validate_uuid(self.target_asset_id, "target_asset_id")

        if self.source_asset_id == self.target_asset_id:
            raise ValueError("Source and target assets must be different.")

    def _validate_relationship_type(self) -> None:
        """Require a valid relationship classification."""

        if not isinstance(self.relationship_type, RelationshipType):
            raise TypeError("relationship_type must be a RelationshipType.")

    def _validate_evidence_references(self) -> None:
        """Validate supporting evidence identifiers."""

        if not isinstance(self.evidence_references, tuple):
            raise TypeError("evidence_references must be a tuple of UUIDs.")

        for reference in self.evidence_references:
            validate_uuid(reference, "evidence_reference")

        if len(set(self.evidence_references)) != len(self.evidence_references):
            raise ValueError("Evidence references must be unique.")

    def _validate_validity(self) -> None:
        """Validate relationship validity timestamps."""

        validate_datetime_interval(
            self.valid_from,
            self.valid_until,
            "valid_from",
            "valid_until",
        )
