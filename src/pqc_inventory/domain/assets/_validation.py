"""Shared validation functions for asset domain objects."""

from datetime import datetime
from uuid import UUID

# ---------------------------------------------------------
# Primitive validation
# ---------------------------------------------------------


def validate_required_text(value: str, field_name: str) -> None:
    """Require a non-empty string."""

    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")

    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty.")


def validate_optional_text(
    value: str | None,
    field_name: str,
) -> None:
    """Validate an optional string."""

    if value is not None:
        validate_required_text(value, field_name)


def validate_positive_integer(
    value: int | None,
    field_name: str,
) -> None:
    """Validate an optional positive integer."""

    if value is not None and (
        isinstance(value, bool) or not isinstance(value, int) or value <= 0
    ):
        raise ValueError(f"{field_name} must be a positive integer.")


def validate_uuid(value: UUID, field_name: str) -> None:
    """Require a UUID value."""

    if not isinstance(value, UUID):
        raise TypeError(f"{field_name} must be a UUID.")


def validate_aware_datetime(
    value: datetime | None,
    field_name: str,
) -> None:
    """Require an optional datetime to be timezone-aware."""

    if value is None:
        return

    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime.")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")


# ---------------------------------------------------------
# Combined validation
# ---------------------------------------------------------


def validate_datetime_interval(
    start: datetime | None,
    end: datetime | None,
    start_name: str,
    end_name: str,
) -> None:
    """Validate optional timezone-aware datetime boundaries."""

    validate_aware_datetime(start, start_name)
    validate_aware_datetime(end, end_name)

    if start is not None and end is not None and start > end:
        raise ValueError(f"{start_name} cannot be later than {end_name}.")
