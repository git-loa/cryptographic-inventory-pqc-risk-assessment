"""Tests for asset identity resolution models."""

from uuid import uuid4

import pytest

from pqc_inventory.application.assets.identity_resolution import (
    IdentityResolutionResult,
    IdentityResolutionStatus,
)


def test_confirmed_match_result():
    """Represent a confirmed match."""

    asset_id = uuid4()

    result = IdentityResolutionResult(
        status=IdentityResolutionStatus.CONFIRMED_MATCH,
        matched_asset_id=asset_id,
        matched_identifier_namespaces=("x509-fingerprint-sha256",),
        reason="Certificate fingerprints match.",
    )

    assert result.matched_asset_id == asset_id
    assert result.status == IdentityResolutionStatus.CONFIRMED_MATCH


def test_possible_match_result():
    """Represent one or more possible matches."""

    candidate_id = uuid4()

    result = IdentityResolutionResult(
        status=IdentityResolutionStatus.POSSIBLE_MATCH,
        candidate_asset_ids=(candidate_id,),
        matched_identifier_namespaces=("purl",),
        reason="Installation context is uncertain.",
    )

    assert result.candidate_asset_ids == (candidate_id,)
    assert result.matched_asset_id is None


@pytest.mark.parametrize(
    "status",
    [
        IdentityResolutionStatus.NO_MATCH,
        IdentityResolutionStatus.INSUFFICIENT_INFORMATION,
    ],
)
def test_unresolved_result_statuses(status):
    """Represent outcomes without confirmed or possible candidates."""

    result = IdentityResolutionResult(
        status=status,
        reason="No reliable matching information is available.",
    )

    assert result.status == status
    assert result.matched_asset_id is None
    assert not result.candidate_asset_ids


def test_confirmed_match_requires_asset_id():
    """Require an existing asset identifier for confirmed matches."""

    with pytest.raises(ValueError, match="matched_asset_id"):
        IdentityResolutionResult(
            status=IdentityResolutionStatus.CONFIRMED_MATCH,
            reason="Confirmed match.",
            matched_identifier_namespaces=("x509-fingerprint-sha256",),
        )


def test_confirmed_match_requires_matching_namespace():
    """Require identifier information for a confirmed match."""

    with pytest.raises(ValueError, match="identifier namespaces"):
        IdentityResolutionResult(
            status=IdentityResolutionStatus.CONFIRMED_MATCH,
            matched_asset_id=uuid4(),
            reason="Confirmed match.",
        )


def test_possible_match_requires_candidates():
    """Require candidate assets for a possible match."""

    with pytest.raises(ValueError, match="candidate asset"):
        IdentityResolutionResult(
            status=IdentityResolutionStatus.POSSIBLE_MATCH,
            matched_identifier_namespaces=("purl",),
            reason="Possible match.",
        )


def test_possible_match_requires_matching_namespace():
    """Require identifier information for a possible match."""

    with pytest.raises(ValueError, match="identifier namespaces"):
        IdentityResolutionResult(
            status=IdentityResolutionStatus.POSSIBLE_MATCH,
            candidate_asset_ids=(uuid4(),),
            reason="Possible match.",
        )


def test_possible_match_cannot_have_confirmed_asset():
    """Prevent confirmed identity and possible candidates together."""

    with pytest.raises(ValueError, match="confirmed matched_asset_id"):
        IdentityResolutionResult(
            status=IdentityResolutionStatus.POSSIBLE_MATCH,
            matched_asset_id=uuid4(),
            candidate_asset_ids=(uuid4(),),
            matched_identifier_namespaces=("purl",),
            reason="Possible match.",
        )


def test_no_match_cannot_contain_candidates():
    """Prevent unresolved candidates from being classified as no match."""

    with pytest.raises(ValueError, match="candidate assets"):
        IdentityResolutionResult(
            status=IdentityResolutionStatus.NO_MATCH,
            candidate_asset_ids=(uuid4(),),
            reason="No match.",
        )


def test_candidate_asset_ids_must_be_unique():
    """Reject duplicate candidate identifiers."""

    candidate_id = uuid4()

    with pytest.raises(ValueError, match="must be unique"):
        IdentityResolutionResult(
            status=IdentityResolutionStatus.POSSIBLE_MATCH,
            candidate_asset_ids=(candidate_id, candidate_id),
            matched_identifier_namespaces=("purl",),
            reason="Possible match.",
        )


def test_invalid_status_is_rejected():
    """Require a valid resolution status."""

    with pytest.raises(TypeError, match="IdentityResolutionStatus"):
        IdentityResolutionResult(
            status="confirmed_match",
            reason="Confirmed match.",
        )


def test_empty_reason_is_rejected():
    """Require an explanation for every resolution result."""

    with pytest.raises(ValueError, match="reason cannot be empty"):
        IdentityResolutionResult(
            status=IdentityResolutionStatus.NO_MATCH,
            reason=" ",
        )


def test_result_is_immutable():
    """Prevent modification of a resolution result."""

    result = IdentityResolutionResult(
        status=IdentityResolutionStatus.NO_MATCH,
        reason="No existing asset matches.",
    )

    with pytest.raises(AttributeError):
        result.status = IdentityResolutionStatus.CONFIRMED_MATCH
