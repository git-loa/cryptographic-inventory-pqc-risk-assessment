"""Tests for asset identifiers."""

from datetime import datetime, timezone
import pytest

from pqc_inventory.domain.assets.identifiers import AssetIdentifier


def test_create_asset_identifier():
    """Create an identifier with all attributes."""

    identifier = AssetIdentifier(
        namespace="hostname",
        value="example.com",
        issuer="DNS",
    )

    assert identifier.namespace == "hostname"
    assert identifier.value == "example.com"
    assert identifier.issuer == "DNS"


def test_create_identifier_without_issuer():
    """Allow identifiers without an issuer."""

    identifier = AssetIdentifier(
        namespace="ip_address",
        value="192.0.2.10",
    )

    assert identifier.issuer is None


@pytest.mark.parametrize(
    "namespace",
    ["", "   "],
)
def test_empty_namespace_is_rejected(namespace):
    """Reject empty or whitespace-only namespaces."""

    with pytest.raises(ValueError, match="namespace"):
        AssetIdentifier(
            namespace=namespace,
            value="example.com",
        )


@pytest.mark.parametrize(
    "namespace",
    [None, 123, True],
)
def test_non_string_namespace_is_rejected(namespace):
    """Require the namespace to be a string."""

    with pytest.raises(TypeError, match="namespace"):
        AssetIdentifier(
            namespace=namespace,
            value="example.com",
        )


@pytest.mark.parametrize(
    "value",
    ["", "   "],
)
def test_empty_identifier_value_is_rejected(value):
    """Reject empty or whitespace-only identifier values."""

    with pytest.raises(ValueError, match="value"):
        AssetIdentifier(
            namespace="hostname",
            value=value,
        )


@pytest.mark.parametrize(
    "value",
    [None, 123, True],
)
def test_non_string_identifier_value_is_rejected(value):
    """Require the identifier value to be a string."""

    with pytest.raises(TypeError, match="value"):
        AssetIdentifier(
            namespace="hostname",
            value=value,
        )


@pytest.mark.parametrize(
    "issuer",
    ["", "   "],
)
def test_empty_issuer_is_rejected(issuer):
    """Reject empty or whitespace-only issuer values."""

    with pytest.raises(ValueError, match="issuer"):
        AssetIdentifier(
            namespace="hostname",
            value="example.com",
            issuer=issuer,
        )


@pytest.mark.parametrize(
    "issuer",
    [123, True],
)
def test_non_string_issuer_is_rejected(issuer):
    """Require the optional issuer to be a string when provided."""

    with pytest.raises(TypeError, match="issuer"):
        AssetIdentifier(
            namespace="hostname",
            value="example.com",
            issuer=issuer,
        )


def test_asset_identifier_is_immutable():
    """Prevent modification of identifier attributes."""

    identifier = AssetIdentifier(
        namespace="hostname",
        value="example.com",
    )

    with pytest.raises(AttributeError):
        identifier.value = "other.com"


def test_asset_identifiers_support_value_equality():
    """Identifiers with identical values should be equal."""

    first = AssetIdentifier(
        namespace="hostname",
        value="example.com",
        issuer="DNS",
    )

    second = AssetIdentifier(
        namespace="hostname",
        value="example.com",
        issuer="DNS",
    )

    assert first == second


def test_different_namespaces_produce_unequal_identifiers():
    """Identifiers in different namespaces should not be equal."""

    first = AssetIdentifier(
        namespace="hostname",
        value="192.0.2.10",
    )

    second = AssetIdentifier(
        namespace="ip_address",
        value="192.0.2.10",
    )

    assert first != second


def test_create_identifier_with_validity_period():
    """Create an identifier with a defined validity period."""

    valid_from = datetime(2026, 1, 1, tzinfo=timezone.utc)
    valid_until = datetime(2026, 6, 1, tzinfo=timezone.utc)

    identifier = AssetIdentifier(
        namespace="ip_address",
        value="192.0.2.10",
        valid_from=valid_from,
        valid_until=valid_until,
    )

    assert identifier.valid_from == valid_from
    assert identifier.valid_until == valid_until


def test_identifier_allows_open_ended_validity_period():
    """Allow an identifier association without an end date."""

    identifier = AssetIdentifier(
        namespace="hostname",
        value="example.com",
        valid_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert identifier.valid_until is None


def test_identifier_allows_unknown_validity_period():
    """Allow identifiers without known validity information."""

    identifier = AssetIdentifier(
        namespace="hostname",
        value="example.com",
    )

    assert identifier.valid_from is None
    assert identifier.valid_until is None


def test_identifier_rejects_naive_validity_datetime():
    """Require timezone-aware validity timestamps."""

    with pytest.raises(ValueError, match="timezone-aware"):
        AssetIdentifier(
            namespace="hostname",
            value="example.com",
            valid_from=datetime(2026, 1, 1),
        )


def test_identifier_rejects_invalid_validity_datetime():
    """Require validity timestamps to be datetime objects."""

    with pytest.raises(TypeError, match="datetime"):
        AssetIdentifier(
            namespace="hostname",
            value="example.com",
            valid_from="2026-01-01",
        )


def test_identifier_rejects_reversed_validity_period():
    """Reject validity periods whose end precedes their start."""

    with pytest.raises(ValueError, match="valid_from"):
        AssetIdentifier(
            namespace="hostname",
            value="example.com",
            valid_from=datetime(2026, 6, 1, tzinfo=timezone.utc),
            valid_until=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )


def test_identifier_validity_fields_are_immutable():
    """Prevent modification of identifier validity timestamps."""

    identifier = AssetIdentifier(
        namespace="hostname",
        value="example.com",
    )

    with pytest.raises(AttributeError):
        identifier.valid_from = datetime(2026, 1, 1, tzinfo=timezone.utc)
