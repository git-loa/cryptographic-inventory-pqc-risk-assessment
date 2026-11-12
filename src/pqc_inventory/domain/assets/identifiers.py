"""External identifiers for cryptographic assets."""

from dataclasses import dataclass
from datetime import datetime

from pqc_inventory.domain.assets._validation import (
    validate_aware_datetime,
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

        validate_aware_datetime(self.valid_from, "valid_from")
        validate_aware_datetime(self.valid_until, "valid_until")

        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_from > self.valid_until
        ):
            raise ValueError("valid_from cannot be later than valid_until.")
