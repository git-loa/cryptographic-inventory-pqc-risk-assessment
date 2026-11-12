"""Tests for shared asset domain validation."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from pqc_inventory.domain.assets._validation import (
    validate_datetime_interval,
    validate_uuid,
)


def test_validate_uuid_accepts_uuid():
    """Accept a valid UUID."""

    value = uuid4()

    validate_uuid(value, "asset_id")


def test_validate_uuid_rejects_invalid_value():
    """Reject values that are not UUID instances."""

    with pytest.raises(TypeError, match="UUID"):
        validate_uuid("invalid", "asset_id")


def test_validate_datetime_interval_accepts_valid_range():
    """Accept chronological timestamps."""

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 2, 1, tzinfo=timezone.utc)

    validate_datetime_interval(start, end, "start", "end")


def test_validate_datetime_interval_accepts_missing_boundaries():
    """Allow unknown start or end timestamps."""

    validate_datetime_interval(None, None, "start", "end")


def test_validate_datetime_interval_rejects_reversed_range():
    """Reject an end timestamp preceding the start."""

    start = datetime(2026, 2, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(ValueError):
        validate_datetime_interval(start, end, "start", "end")
