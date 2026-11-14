"""Resolve discovered assets against existing inventory assets."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import NamedTuple
from uuid import UUID

from pqc_inventory.application.assets.identifier_normalization import (
    X509_FINGERPRINT_LEGACY_NAMESPACES,
    X509_FINGERPRINT_NAMESPACES,
    normalize_identifier,
)
from pqc_inventory.domain.assets.asset import Asset
from pqc_inventory.domain.assets.enums import AssetType

# ---------------------------------------------------------
# Shared validation
# ---------------------------------------------------------


def _validate_unique_tuple(
    values: object,
    expected_type: type,
    field_name: str,
) -> None:
    """Validate a tuple containing unique values of the expected type."""

    if not isinstance(values, tuple):
        raise TypeError(f"{field_name} must be a tuple.")

    if any(not isinstance(value, expected_type) for value in values):
        raise TypeError(
            f"All {field_name} entries must be {expected_type.__name__} values."
        )

    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} entries must be unique.")


def _validate_required_text(value: str, field_name: str) -> None:
    """Require non-empty text."""

    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")

    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty.")


# ---------------------------------------------------------
# Resolution result
# ---------------------------------------------------------


class IdentityResolutionStatus(StrEnum):
    """Represent the outcome of asset identity resolution."""

    CONFIRMED_MATCH = "confirmed_match"
    POSSIBLE_MATCH = "possible_match"
    NO_MATCH = "no_match"
    INSUFFICIENT_INFORMATION = "insufficient_information"


@dataclass(frozen=True, slots=True)
class IdentityResolutionResult:
    """Record the outcome of an asset identity resolution attempt."""

    status: IdentityResolutionStatus
    reason: str

    matched_asset_id: UUID | None = None
    candidate_asset_ids: tuple[UUID, ...] = ()
    matched_identifier_namespaces: tuple[str, ...] = ()
    conflicting_identifier_namespaces: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate the resolution result."""

        if not isinstance(self.status, IdentityResolutionStatus):
            raise TypeError("status must be an IdentityResolutionStatus.")

        _validate_required_text(self.reason, "reason")

        if self.matched_asset_id is not None and not isinstance(
            self.matched_asset_id,
            UUID,
        ):
            raise TypeError("matched_asset_id must be a UUID or None.")

        _validate_unique_tuple(
            self.candidate_asset_ids,
            UUID,
            "candidate_asset_ids",
        )

        _validate_unique_tuple(
            self.matched_identifier_namespaces,
            str,
            "matched_identifier_namespaces",
        )

        _validate_unique_tuple(
            self.conflicting_identifier_namespaces,
            str,
            "conflicting_identifier_namespaces",
        )

        self._validate_result_consistency()

    def _validate_result_consistency(self) -> None:
        """Ensure result attributes agree with the resolution status."""

        if self.status == IdentityResolutionStatus.CONFIRMED_MATCH:
            if self.matched_asset_id is None:
                raise ValueError("A confirmed match requires matched_asset_id.")

            if self.candidate_asset_ids:
                raise ValueError(
                    "A confirmed match cannot contain unresolved candidates."
                )

            if not self.matched_identifier_namespaces:
                raise ValueError(
                    "A confirmed match requires matching identifier namespaces."
                )

            if self.conflicting_identifier_namespaces:
                raise ValueError(
                    "A confirmed match cannot contain conflicting identifiers."
                )

            return

        if self.matched_asset_id is not None:
            raise ValueError("Only a confirmed match can have matched_asset_id.")

        if self.status == IdentityResolutionStatus.POSSIBLE_MATCH:
            if not self.candidate_asset_ids:
                raise ValueError(
                    "A possible match requires at least one candidate asset."
                )

            if not (
                self.matched_identifier_namespaces
                or self.conflicting_identifier_namespaces
            ):
                raise ValueError(
                    "A possible match requires matching or conflicting "
                    "identifier information."
                )

            return

        if self.status == IdentityResolutionStatus.NO_MATCH:
            if (
                self.candidate_asset_ids
                or self.matched_identifier_namespaces
                or self.conflicting_identifier_namespaces
            ):
                raise ValueError(
                    "A no-match result cannot contain matching candidates "
                    "or identifier information."
                )

            return

        # INSUFFICIENT_INFORMATION may retain candidate IDs that
        # could not be compared reliably.
        if self.matched_identifier_namespaces or self.conflicting_identifier_namespaces:
            raise ValueError(
                "An insufficient-information result cannot contain "
                "matched or conflicting identifiers."
            )


# ---------------------------------------------------------
# Candidate comparison
# ---------------------------------------------------------


class _CandidateMatchStatus(StrEnum):
    """Represent the comparison outcome for one candidate."""

    CONFIRMED = "confirmed"
    POSSIBLE = "possible"
    DIFFERENT = "different"
    UNCOMPARABLE = "uncomparable"


class _CandidateFingerprintComparison(NamedTuple):
    """Record fingerprint comparison results for one candidate."""

    status: _CandidateMatchStatus
    matched_namespaces: frozenset[str]
    conflicting_namespaces: frozenset[str]


@dataclass(slots=True)
class _CertificateMatchSummary:
    """Accumulate certificate candidate comparison results."""

    confirmed_asset_ids: set[UUID] = field(default_factory=set)
    possible_asset_ids: set[UUID] = field(default_factory=set)
    uncomparable_asset_ids: set[UUID] = field(default_factory=set)

    matched_namespaces: set[str] = field(default_factory=set)
    conflicting_namespaces: set[str] = field(default_factory=set)

    def record(
        self,
        asset_id: UUID,
        comparison: _CandidateFingerprintComparison,
    ) -> None:
        """Record one candidate comparison."""

        if comparison.status == _CandidateMatchStatus.CONFIRMED:
            self.confirmed_asset_ids.add(asset_id)
            self.matched_namespaces.update(comparison.matched_namespaces)

        elif comparison.status == _CandidateMatchStatus.POSSIBLE:
            self.possible_asset_ids.add(asset_id)
            self.matched_namespaces.update(comparison.matched_namespaces)
            self.conflicting_namespaces.update(comparison.conflicting_namespaces)

        elif comparison.status == _CandidateMatchStatus.UNCOMPARABLE:
            self.uncomparable_asset_ids.add(asset_id)

        # DIFFERENT candidates do not contribute to a matching result.


# ---------------------------------------------------------
# Asset identity resolver
# ---------------------------------------------------------


class AssetIdentityResolver:  # pylint: disable=too-few-public-methods
    """Resolve certificate assets against existing inventory assets."""

    def resolve(
        self,
        discovered_asset: Asset,
        candidate_assets: Sequence[Asset],
    ) -> IdentityResolutionResult:
        """Resolve a discovered certificate against existing candidates.

        The initial implementation supports X.509 certificate identity
        through algorithm-qualified certificate fingerprints.
        """

        self._validate_inputs(discovered_asset, candidate_assets)

        if discovered_asset.asset_type != AssetType.CERTIFICATE:
            raise NotImplementedError(
                "Identity resolution currently supports certificates only."
            )

        discovered_fingerprints = self._get_certificate_fingerprints(discovered_asset)

        if not discovered_fingerprints:
            return IdentityResolutionResult(
                status=IdentityResolutionStatus.INSUFFICIENT_INFORMATION,
                reason=(
                    "The discovered certificate has no supported "
                    "fingerprint identifier."
                ),
            )

        return self._resolve_certificate(
            discovered_fingerprints,
            candidate_assets,
        )

    @staticmethod
    def _validate_inputs(
        discovered_asset: Asset,
        candidate_assets: Sequence[Asset],
    ) -> None:
        """Validate resolver input objects."""

        if not isinstance(discovered_asset, Asset):
            raise TypeError("discovered_asset must be an Asset.")

        if isinstance(candidate_assets, (str, bytes)) or not isinstance(
            candidate_assets,
            Sequence,
        ):
            raise TypeError("candidate_assets must be a sequence of Assets.")

        candidate_ids: set[UUID] = set()

        for candidate in candidate_assets:
            if not isinstance(candidate, Asset):
                raise TypeError("Every candidate must be an Asset.")

            if candidate.asset_id in candidate_ids:
                raise ValueError("Candidate asset identifiers must be unique.")

            candidate_ids.add(candidate.asset_id)

    @staticmethod
    def _get_certificate_fingerprints(
        asset: Asset,
    ) -> dict[str, str]:
        """Return normalized fingerprints indexed by namespace."""

        fingerprints: dict[str, str] = {}

        for identifier in asset.identifiers:
            if identifier.namespace not in X509_FINGERPRINT_NAMESPACES:
                continue

            normalized = normalize_identifier(identifier)

            existing_value = fingerprints.get(identifier.namespace)

            if existing_value is not None and existing_value != normalized:
                raise ValueError(
                    "A certificate cannot have conflicting values "
                    f"for fingerprint namespace {identifier.namespace!r}."
                )

            fingerprints[identifier.namespace] = normalized

        return fingerprints

    @staticmethod
    def _compare_certificate_fingerprints(
        discovered: dict[str, str],
        candidate: dict[str, str],
    ) -> _CandidateFingerprintComparison:
        """Compare fingerprint values shared by two certificates."""

        shared_namespaces = discovered.keys() & candidate.keys()

        if not shared_namespaces:
            return _CandidateFingerprintComparison(
                _CandidateMatchStatus.UNCOMPARABLE,
                frozenset(),
                frozenset(),
            )

        matched = frozenset(
            namespace
            for namespace in shared_namespaces
            if discovered[namespace] == candidate[namespace]
        )

        conflicting = frozenset(
            namespace
            for namespace in shared_namespaces
            if discovered[namespace] != candidate[namespace]
        )

        strong_matches = matched - X509_FINGERPRINT_LEGACY_NAMESPACES
        strong_conflicts = conflicting - X509_FINGERPRINT_LEGACY_NAMESPACES

        if strong_conflicts:
            status = (
                _CandidateMatchStatus.POSSIBLE
                if strong_matches
                else _CandidateMatchStatus.DIFFERENT
            )

        elif strong_matches:
            status = (
                _CandidateMatchStatus.POSSIBLE
                if conflicting
                else _CandidateMatchStatus.CONFIRMED
            )

        elif matched:
            # A matching legacy fingerprint cannot independently confirm identity.
            status = _CandidateMatchStatus.POSSIBLE

        else:
            status = _CandidateMatchStatus.DIFFERENT

        return _CandidateFingerprintComparison(
            status,
            matched,
            conflicting,
        )

    def _resolve_certificate(
        self,
        discovered_fingerprints: dict[str, str],
        candidate_assets: Sequence[Asset],
    ) -> IdentityResolutionResult:
        """Evaluate existing certificate candidates."""

        summary = _CertificateMatchSummary()

        for candidate in candidate_assets:
            if candidate.asset_type != AssetType.CERTIFICATE:
                continue

            candidate_fingerprints = self._get_certificate_fingerprints(candidate)

            comparison = self._compare_certificate_fingerprints(
                discovered_fingerprints,
                candidate_fingerprints,
            )

            summary.record(candidate.asset_id, comparison)

        return self._build_certificate_result(summary)

    @staticmethod
    def _build_certificate_result(
        summary: _CertificateMatchSummary,
    ) -> IdentityResolutionResult:
        """Build the final identity-resolution result."""

        confirmed_ids = summary.confirmed_asset_ids
        possible_ids = summary.possible_asset_ids
        uncomparable_ids = summary.uncomparable_asset_ids

        if len(confirmed_ids) == 1 and not possible_ids and not uncomparable_ids:
            return IdentityResolutionResult(
                status=IdentityResolutionStatus.CONFIRMED_MATCH,
                matched_asset_id=next(iter(confirmed_ids)),
                matched_identifier_namespaces=tuple(sorted(summary.matched_namespaces)),
                reason=(
                    "A strong certificate fingerprint matches exactly "
                    "one existing certificate asset."
                ),
            )

        candidate_ids = tuple(
            sorted(
                confirmed_ids | possible_ids | uncomparable_ids,
                key=str,
            )
        )

        if confirmed_ids or possible_ids:
            return IdentityResolutionResult(
                status=IdentityResolutionStatus.POSSIBLE_MATCH,
                candidate_asset_ids=candidate_ids,
                matched_identifier_namespaces=tuple(sorted(summary.matched_namespaces)),
                conflicting_identifier_namespaces=tuple(
                    sorted(summary.conflicting_namespaces)
                ),
                reason=(
                    "One or more existing certificate records require "
                    "review because the available fingerprint information "
                    "does not establish one unambiguous match."
                ),
            )

        if uncomparable_ids:
            return IdentityResolutionResult(
                status=IdentityResolutionStatus.INSUFFICIENT_INFORMATION,
                candidate_asset_ids=tuple(sorted(uncomparable_ids, key=str)),
                reason=(
                    "Existing certificate candidates could not be compared "
                    "because they do not share a supported fingerprint namespace."
                ),
            )

        return IdentityResolutionResult(
            status=IdentityResolutionStatus.NO_MATCH,
            reason=("No existing certificate has a matching strong fingerprint."),
        )
