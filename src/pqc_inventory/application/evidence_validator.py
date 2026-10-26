"""Validation of TLS evidence before security assessment."""

import math
from typing import cast

from pqc_inventory.collection.models import TLSScanResult
from pqc_inventory.collection.tls_utils import validate_target


class EvidenceValidator:  # pylint: disable=too-few-public-methods
    """Validate the structure and fields of collected TLS evidence."""

    REQUIRED_FIELDS = {
        "schema_version",
        "scan_id",
        "target",
        "target_type",
        "port",
        "resolved_ip_address",
        "scan_status",
        "started_at",
        "completed_at",
        "scan_time_seconds",
        "certificate_verification_status",
        "certificate_verification_error",
        "key_establishment_evidence_status",
        "diagnostics",
    }

    ALLOWED_SCAN_STATUSES = {
        "completed",
        "partial",
        "failed",
    }

    ALLOWED_CERTIFICATE_STATUSES = {
        "verified",
        "failed",
        "not_performed",
        "unknown",
    }

    ALLOWED_KEY_ESTABLISHMENT_STATUSES = {
        "observed",
        "unavailable",
        "not_attempted",
    }

    ALLOWED_TARGET_TYPES = {
        "domain",
        "ipv4",
        "ipv6",
    }

    ALLOWED_DIAGNOSTIC_CATEGORIES = {
        "input_validation",
        "connection",
        "timeout",
        "certificate",
        "key_establishment",
        "parsing",
        "internal",
    }

    ALLOWED_DIAGNOSTIC_SEVERITIES = {
        "info",
        "warning",
        "error",
    }

    REQUIRED_DIAGNOSTIC_FIELDS = {
        "code",
        "category",
        "severity",
        "message",
        "stage",
    }

    @classmethod
    def validate(cls, data: object) -> list[TLSScanResult]:
        """Validate and normalize a collection of TLS evidence.

        Args:
            data: A TLS evidence JSON object or a list of such objects.

        Returns:
            A list containing validated TLS scan results.

        Raises:
            ValueError: If the evidence structure or any required field
                is invalid.
        """
        if isinstance(data, dict):
            evidence_items = [data]
        elif isinstance(data, list):
            evidence_items = data
        else:
            raise ValueError(
                "TLS evidence must be a JSON object or a list of JSON objects."
            )

        if not evidence_items:
            raise ValueError("The TLS evidence file contains no scan results.")

        return [
            cls._validate_item(item, index) for index, item in enumerate(evidence_items)
        ]

    @classmethod
    def _validate_item(
        cls,
        item: object,
        index: int,
    ) -> TLSScanResult:
        """Validate an individual TLS evidence record."""
        if not isinstance(item, dict):
            raise ValueError(f"TLS evidence entry {index} must be a JSON object.")

        evidence = cast(dict[str, object], item)

        cls._validate_required_fields(evidence, index)
        cls._validate_target_fields(evidence, index)
        cls._validate_port(evidence["port"], index)
        cls._validate_metadata(evidence, index)
        cls._validate_status_fields(evidence, index)
        cls._validate_diagnostics(evidence["diagnostics"], index)

        return cast(TLSScanResult, evidence)

    @classmethod
    def _validate_required_fields(
        cls,
        evidence: dict[str, object],
        index: int,
    ) -> None:
        """Ensure that all mandatory evidence fields are present."""
        missing_fields = cls.REQUIRED_FIELDS - evidence.keys()

        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(
                f"TLS evidence entry {index} is missing required fields: " f"{missing}."
            )

    @classmethod
    def _validate_target_fields(
        cls,
        evidence: dict[str, object],
        index: int,
    ) -> None:
        """Validate the target and its declared type."""
        target = evidence["target"]

        if not isinstance(target, str) or not target.strip():
            raise ValueError(
                f"TLS evidence entry {index} has an invalid target: "
                "expected a non-empty IP address or DNS hostname."
            )

        try:
            detected_type, _ = validate_target(target)
        except ValueError as exc:
            raise ValueError(
                f"TLS evidence entry {index} has an invalid target "
                f"'{target}': {exc}"
            ) from exc

        target_type = evidence["target_type"]

        if target_type not in cls.ALLOWED_TARGET_TYPES:
            raise ValueError(f"TLS evidence entry {index} has an invalid target_type.")

        if target_type != detected_type:
            raise ValueError(
                f"TLS evidence entry {index} has a target_type mismatch: "
                f"target '{target}' is classified as '{detected_type}', "
                f"not '{target_type}'."
            )

    @staticmethod
    def _validate_port(port: object, index: int) -> None:
        """Require a valid TCP port number."""
        if (
            isinstance(port, bool)
            or not isinstance(port, int)
            or not 1 <= port <= 65535
        ):
            raise ValueError(f"TLS evidence entry {index} has an invalid port.")

    @staticmethod
    def _validate_metadata(
        evidence: dict[str, object],
        index: int,
    ) -> None:
        """Validate required strings, nullable strings, and scan duration."""
        required_strings = (
            "schema_version",
            "scan_id",
            "started_at",
        )

        for field in required_strings:
            value = evidence[field]

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"TLS evidence entry {index} has an invalid " f"'{field}' field."
                )

        nullable_strings = (
            "resolved_ip_address",
            "completed_at",
            "certificate_verification_error",
        )

        for field in nullable_strings:
            value = evidence[field]

            if value is not None and not isinstance(value, str):
                raise ValueError(
                    f"TLS evidence entry {index} has an invalid " f"'{field}' field."
                )

        scan_time = evidence["scan_time_seconds"]

        if (
            isinstance(scan_time, bool)
            or not isinstance(scan_time, (int, float))
            or not math.isfinite(scan_time)
            or scan_time < 0
        ):
            raise ValueError(
                f"TLS evidence entry {index} has an invalid "
                "'scan_time_seconds' field."
            )

    @classmethod
    def _validate_status_fields(
        cls,
        evidence: dict[str, object],
        index: int,
    ) -> None:
        """Validate the permitted values of status fields."""
        allowed_values = {
            "scan_status": cls.ALLOWED_SCAN_STATUSES,
            "certificate_verification_status": (cls.ALLOWED_CERTIFICATE_STATUSES),
            "key_establishment_evidence_status": (
                cls.ALLOWED_KEY_ESTABLISHMENT_STATUSES
            ),
        }

        for field, permitted_values in allowed_values.items():
            value = evidence[field]

            if not isinstance(value, str) or value not in permitted_values:
                raise ValueError(
                    f"TLS evidence entry {index} has an invalid " f"'{field}' field."
                )

    @classmethod
    def _validate_diagnostics(
        cls,
        diagnostics: object,
        index: int,
    ) -> None:
        """Validate the structure and values of scan diagnostics."""
        if not isinstance(diagnostics, list):
            raise ValueError(
                f"TLS evidence entry {index} has invalid diagnostics: "
                "expected a list."
            )

        for diagnostic_index, diagnostic in enumerate(diagnostics):
            if not isinstance(diagnostic, dict):
                raise ValueError(
                    f"TLS evidence entry {index}, diagnostic "
                    f"{diagnostic_index}, must be a JSON object."
                )

            diagnostic_data = cast(dict[str, object], diagnostic)

            cls._validate_diagnostic_fields(
                diagnostic_data,
                index,
                diagnostic_index,
            )

    @classmethod
    def _validate_diagnostic_fields(
        cls,
        diagnostic: dict[str, object],
        evidence_index: int,
        diagnostic_index: int,
    ) -> None:
        """Validate the required fields of one diagnostic."""
        missing_fields = cls.REQUIRED_DIAGNOSTIC_FIELDS - diagnostic.keys()

        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(
                f"TLS evidence entry {evidence_index}, diagnostic "
                f"{diagnostic_index}, is missing fields: {missing}."
            )

        for field in ("code", "message", "stage"):
            if not isinstance(diagnostic[field], str):
                raise ValueError(
                    f"TLS evidence entry {evidence_index}, diagnostic "
                    f"{diagnostic_index}, has an invalid '{field}'."
                )

        category = diagnostic["category"]

        if (
            not isinstance(category, str)
            or category not in cls.ALLOWED_DIAGNOSTIC_CATEGORIES
        ):
            raise ValueError(
                f"TLS evidence entry {evidence_index}, diagnostic "
                f"{diagnostic_index}, has an invalid category."
            )

        severity = diagnostic["severity"]

        if (
            not isinstance(severity, str)
            or severity not in cls.ALLOWED_DIAGNOSTIC_SEVERITIES
        ):
            raise ValueError(
                f"TLS evidence entry {evidence_index}, diagnostic "
                f"{diagnostic_index}, has an invalid severity."
            )
