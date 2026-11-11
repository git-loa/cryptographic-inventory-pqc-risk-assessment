"""External identifiers for cryptographic assets."""

from dataclasses import dataclass

from pqc_inventory.domain.assets._validation import (
    validate_required_text,
    validate_optional_text,
)


@dataclass(frozen=True, slots=True)
class AssetIdentifier:
    """Represent a namespaced external identifier."""

    namespace: str
    value: str
    issuer: str | None = None

    def __post_init__(self) -> None:
        """Validate external identifier attributes."""

        validate_required_text(self.namespace, "namespace")
        validate_required_text(self.value, "value")
        validate_optional_text(self.issuer, "issuer")
