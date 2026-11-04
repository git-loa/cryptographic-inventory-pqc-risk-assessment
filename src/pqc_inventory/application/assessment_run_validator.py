"""Validation of saved cryptographic assessment runs."""

from typing import cast

from pqc_inventory.application.evidence_validator import EvidenceValidator
from pqc_inventory.assessment.models import AssessmentRun


class AssessmentRunValidator:  # pylint: disable=too-few-public-methods
    """Validate the structure and consistency of assessment runs."""

    REQUIRED_FIELDS = {
        "schema_version",
        "assessment_run_id",
        "domain",
        "created_at",
        "methodology_version",
        "evidence",
        "assessments",
    }

    ALLOWED_EXECUTION_STATUSES = {
        "completed",
        "partial",
        "not_assessed",
        "failed",
    }

    ALLOWED_CLASSIFICATIONS = {
        "acceptable",
        "acceptable_with_review",
        "unacceptable",
        "unknown",
    }

    @classmethod
    def validate(cls, data: object) -> list[AssessmentRun]:
        """Validate one assessment run or a list of assessment runs.

        Args:
            data: An assessment-run JSON object or a list of objects.

        Returns:
            A list of validated assessment runs.

        Raises:
            ValueError: If the input structure or any assessment run
                is invalid.
        """
        if isinstance(data, dict):
            assessment_items = [data]
        elif isinstance(data, list):
            assessment_items = data
        else:
            raise ValueError(
                "Assessment data must be a JSON object or a list of objects."
            )

        if not assessment_items:
            raise ValueError("The assessment file contains no assessment runs.")

        return [
            cls._validate_item(item, index)
            for index, item in enumerate(assessment_items)
        ]

    @classmethod
    def _validate_item(
        cls,
        item: object,
        index: int,
    ) -> AssessmentRun:
        """Validate an individual assessment run."""
        if not isinstance(item, dict):
            raise ValueError(f"Assessment run {index} must be a JSON object.")

        assessment = cast(dict[str, object], item)

        cls._validate_required_fields(assessment, index)
        cls._validate_metadata(assessment, index)
        cls._validate_evidence(assessment, index)
        cls._validate_assessments(assessment["assessments"], index)

        return cast(AssessmentRun, assessment)

    @classmethod
    def _validate_required_fields(
        cls,
        assessment: dict[str, object],
        index: int,
    ) -> None:
        """Ensure all mandatory assessment fields are present."""
        missing_fields = cls.REQUIRED_FIELDS - assessment.keys()

        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(
                f"Assessment run {index} is missing required fields: {missing}."
            )

    @staticmethod
    def _validate_metadata(
        assessment: dict[str, object],
        index: int,
    ) -> None:
        """Validate assessment-run metadata."""
        required_strings = (
            "schema_version",
            "assessment_run_id",
            "domain",
            "created_at",
            "methodology_version",
        )

        for field in required_strings:
            value = assessment[field]

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Assessment run {index} has an invalid '{field}' field."
                )

    @staticmethod
    def _validate_evidence(
        assessment: dict[str, object],
        index: int,
    ) -> None:
        """Validate embedded TLS evidence and its relationship to the run."""

        evidence = assessment["evidence"]

        if not isinstance(evidence, dict):
            raise ValueError(
                f"Assessment run {index} has invalid evidence: "
                "expected a JSON object."
            )

        try:
            validated_evidence = EvidenceValidator.validate(evidence)
        except ValueError as exc:
            raise ValueError(
                f"Assessment run {index} contains invalid TLS evidence: {exc}"
            ) from exc

        if len(validated_evidence) != 1:
            raise ValueError(
                f"Assessment run {index} must contain exactly one TLS evidence record."
            )

        evidence_target = validated_evidence[0]["target"]

        if assessment["domain"] != evidence_target:
            raise ValueError(
                f"Assessment run {index} has a domain mismatch: "
                f"'{assessment['domain']}' does not match "
                f"the evidence target '{evidence_target}'."
            )

    @classmethod
    def _validate_assessments(
        cls,
        assessments: object,
        index: int,
    ) -> None:
        """Validate the collection of policy results."""
        if not isinstance(assessments, dict):
            raise ValueError(
                f"Assessment run {index} has invalid assessments: "
                "expected a JSON object."
            )

        for policy_id, policy_result in assessments.items():
            if not isinstance(policy_id, str) or not policy_id.strip():
                raise ValueError(
                    f"Assessment run {index} contains an invalid policy identifier."
                )

            cls._validate_policy_result(
                policy_result,
                policy_id,
                index,
            )

    @classmethod
    def _validate_policy_result(
        cls,
        policy_result: object,
        policy_id: str,
        index: int,
    ) -> None:
        """Validate one policy execution result."""
        if not isinstance(policy_result, dict):
            raise ValueError(
                f"Assessment run {index}, policy '{policy_id}' "
                "must be a JSON object."
            )

        result = cast(dict[str, object], policy_result)

        required_fields = {
            "policy_id",
            "policy_version",
            "execution_status",
            "findings",
            "limitations",
        }

        missing_fields = required_fields - result.keys()

        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(
                f"Assessment run {index}, policy '{policy_id}' "
                f"is missing fields: {missing}."
            )

        for field in ("policy_id", "policy_version"):
            value = result[field]

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Assessment run {index}, policy '{policy_id}' "
                    f"has an invalid '{field}' field."
                )

        if result["policy_id"] != policy_id:
            raise ValueError(
                f"Assessment run {index} has a policy identifier mismatch: "
                f"dictionary key '{policy_id}' does not match "
                f"result policy ID '{result['policy_id']}'."
            )

        execution_status = result["execution_status"]

        if (
            not isinstance(execution_status, str)
            or execution_status not in cls.ALLOWED_EXECUTION_STATUSES
        ):
            raise ValueError(
                f"Assessment run {index}, policy '{policy_id}' "
                "has an invalid execution_status."
            )

        cls._validate_string_list(
            result["limitations"],
            "limitations",
            index,
            policy_id,
        )

        findings = result["findings"]

        if not isinstance(findings, list):
            raise ValueError(
                f"Assessment run {index}, policy '{policy_id}' "
                "has invalid findings: expected a list."
            )

        for finding_index, finding in enumerate(findings):
            cls._validate_finding(
                finding,
                policy_id,
                index,
                finding_index,
            )

    @classmethod
    def _validate_finding(
        cls,
        finding: object,
        policy_id: str,
        assessment_index: int,
        finding_index: int,
    ) -> None:
        """Validate one assessment finding."""
        if not isinstance(finding, dict):
            raise ValueError(
                f"Assessment run {assessment_index}, policy '{policy_id}', "
                f"finding {finding_index} must be a JSON object."
            )

        finding_data = cast(dict[str, object], finding)

        required_fields = {
            "finding_id",
            "policy_id",
            "dimension",
            "observed_value",
            "classification",
            "rule_id",
            "rationale",
            "evidence_references",
        }

        missing_fields = required_fields - finding_data.keys()

        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(
                f"Assessment run {assessment_index}, policy '{policy_id}', "
                f"finding {finding_index} is missing fields: {missing}."
            )

        required_strings = (
            "finding_id",
            "policy_id",
            "dimension",
            "rule_id",
            "rationale",
        )

        for field in required_strings:
            value = finding_data[field]

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Assessment run {assessment_index}, policy '{policy_id}', "
                    f"finding {finding_index} has an invalid '{field}' field."
                )

        if finding_data["policy_id"] != policy_id:
            raise ValueError(
                f"Assessment run {assessment_index}, policy '{policy_id}', "
                f"finding {finding_index} has a policy identifier mismatch."
            )

        observed_value = finding_data["observed_value"]

        if observed_value is not None and not isinstance(observed_value, str):
            raise ValueError(
                f"Assessment run {assessment_index}, policy '{policy_id}', "
                f"finding {finding_index} has an invalid observed_value."
            )

        classification = finding_data["classification"]

        if (
            not isinstance(classification, str)
            or classification not in cls.ALLOWED_CLASSIFICATIONS
        ):
            raise ValueError(
                f"Assessment run {assessment_index}, policy '{policy_id}', "
                f"finding {finding_index} has an invalid classification."
            )

        cls._validate_string_list(
            finding_data["evidence_references"],
            "evidence_references",
            assessment_index,
            policy_id,
            finding_index,
        )

    @staticmethod
    def _validate_string_list(
        value: object,
        field: str,
        assessment_index: int,
        policy_id: str,
        finding_index: int | None = None,
    ) -> None:
        """Validate a list containing non-empty strings."""
        if not isinstance(value, list):
            raise ValueError(
                f"Assessment run {assessment_index}, policy '{policy_id}' "
                f"has an invalid '{field}': expected a list."
            )

        for item_index, item in enumerate(value):
            if not isinstance(item, str) or not item.strip():
                location = (
                    f", finding {finding_index}" if finding_index is not None else ""
                )

                raise ValueError(
                    f"Assessment run {assessment_index}, policy '{policy_id}'"
                    f"{location} has an invalid '{field}' entry at index "
                    f"{item_index}."
                )
