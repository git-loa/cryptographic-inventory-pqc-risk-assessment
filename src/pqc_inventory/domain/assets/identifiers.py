"""External identifiers for cryptographic assets."""

from dataclasses import dataclass
from datetime import datetime

from pqc_inventory.domain.assets._validation import (
    validate_datetime_interval,
    validate_optional_text,
    validate_required_text,
)


@dataclass(frozen=True, slots=True)
class AssetIdentifier:
    """Represent a namespaced external identifier."""

    namespace: str
    value: str
    issuer: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    def __post_init__(self) -> None:
        """Validate external identifier attributes."""

        validate_required_text(self.namespace, "namespace")
        validate_required_text(self.value, "value")
        validate_optional_text(self.issuer, "issuer")

        validate_datetime_interval(
            self.valid_from,
            self.valid_until,
            "valid_from",
            "valid_until",
        )
