"""Tests for saved assessment-run validation."""

import pytest

from pqc_inventory.application.assessment_run_validator import (
    AssessmentRunValidator,
)


def test_validate_single_assessment_run(
    assessment_run_factory,
    policy_execution_record_factory,
):
    """Accept one structurally valid assessment run."""

    assessment_run = assessment_run_factory(
        assessments={
            "A1": policy_execution_record_factory(policy_id="A1"),
        },
    )

    result = AssessmentRunValidator.validate(assessment_run)

    assert len(result) == 1
    assert result[0] == assessment_run


def test_validate_multiple_assessment_runs(
    assessment_run_factory,
    policy_execution_record_factory,
):
    """Accept a list containing multiple valid assessment runs."""

    assessment_runs = [
        assessment_run_factory(
            assessment_run_id="run-001",
            assessments={
                "A1": policy_execution_record_factory(policy_id="A1"),
            },
        ),
        assessment_run_factory(
            assessment_run_id="run-002",
            domain="example.org",
            assessments={
                "A1": policy_execution_record_factory(policy_id="A1"),
            },
        ),
    ]

    result = AssessmentRunValidator.validate(assessment_runs)

    assert len(result) == 2
    assert result[0]["assessment_run_id"] == "run-001"
    assert result[1]["assessment_run_id"] == "run-002"


def test_reject_empty_assessment_list():
    """Reject an empty collection of assessment runs."""

    with pytest.raises(ValueError, match="contains no assessment runs"):
        AssessmentRunValidator.validate([])


@pytest.mark.parametrize(
    "invalid_data",
    [
        None,
        "invalid",
        123,
        True,
    ],
)
def test_reject_invalid_top_level_input(invalid_data):
    """Reject unsupported top-level input types."""

    with pytest.raises(ValueError, match="must be a JSON object"):
        AssessmentRunValidator.validate(invalid_data)


def test_reject_non_dictionary_assessment_item():
    """Reject an invalid item inside an assessment-run list."""

    with pytest.raises(ValueError, match="must be a JSON object"):
        AssessmentRunValidator.validate([None])


def test_reject_missing_required_field(
    assessment_run_factory,
    policy_execution_record_factory,
):
    """Reject an assessment run missing a mandatory field."""

    assessment_run = assessment_run_factory(
        assessments={
            "A1": policy_execution_record_factory(policy_id="A1"),
        },
    )
    assessment_run.pop("methodology_version")

    with pytest.raises(ValueError, match="methodology_version"):
        AssessmentRunValidator.validate(assessment_run)


@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("schema_version", ""),
        ("assessment_run_id", None),
        ("domain", ""),
        ("created_at", 123),
        ("methodology_version", ""),
    ],
)
def test_reject_invalid_metadata(
    assessment_run_factory,
    policy_execution_record_factory,
    field,
    invalid_value,
):
    """Reject invalid assessment-run metadata."""

    assessment_run = assessment_run_factory(
        assessments={
            "A1": policy_execution_record_factory(policy_id="A1"),
        },
    )
    assessment_run[field] = invalid_value

    with pytest.raises(ValueError, match=field):
        AssessmentRunValidator.validate(assessment_run)


def test_reject_invalid_embedded_tls_evidence(
    assessment_run_factory,
    policy_execution_record_factory,
):
    """Reject malformed TLS evidence."""

    assessment_run = assessment_run_factory(
        assessments={
            "A1": policy_execution_record_factory(policy_id="A1"),
        },
    )
    assessment_run["evidence"]["port"] = 70000

    with pytest.raises(ValueError, match="invalid TLS evidence"):
        AssessmentRunValidator.validate(assessment_run)


def test_reject_evidence_as_list(
    assessment_run_factory,
    policy_execution_record_factory,
):
    """Require embedded evidence to be a single JSON object."""

    assessment_run = assessment_run_factory(
        assessments={
            "A1": policy_execution_record_factory(policy_id="A1"),
        },
    )
    assessment_run["evidence"] = [assessment_run["evidence"]]

    with pytest.raises(ValueError, match="expected a JSON object"):
        AssessmentRunValidator.validate(assessment_run)


def test_reject_domain_evidence_mismatch(
    assessment_run_factory,
    policy_execution_record_factory,
):
    """Ensure the assessment domain matches the TLS evidence target."""

    assessment_run = assessment_run_factory(
        domain="example.org",
        assessments={
            "A1": policy_execution_record_factory(policy_id="A1"),
        },
    )

    assessment_run["evidence"]["target"] = "different.example"

    with pytest.raises(ValueError, match="domain mismatch"):
        AssessmentRunValidator.validate(assessment_run)


def test_reject_invalid_assessments_structure(
    assessment_run_factory,
):
    """Require assessments to be represented by a dictionary."""

    assessment_run = assessment_run_factory()
    assessment_run["assessments"] = []

    with pytest.raises(ValueError, match="expected a JSON object"):
        AssessmentRunValidator.validate(assessment_run)


def test_reject_policy_identifier_mismatch(
    assessment_run_factory,
    policy_execution_record_factory,
):
    """Ensure policy dictionary keys match their result identifiers."""

    assessment_run = assessment_run_factory(
        assessments={
            "A1": policy_execution_record_factory(policy_id="A2"),
        },
    )

    with pytest.raises(ValueError, match="identifier mismatch"):
        AssessmentRunValidator.validate(assessment_run)


def test_reject_invalid_policy_execution_status(
    assessment_run_factory,
    policy_execution_record_factory,
):
    """Reject unsupported policy execution statuses."""

    assessment_run = assessment_run_factory(
        assessments={
            "A1": policy_execution_record_factory(
                policy_id="A1",
                execution_status="invalid",
            ),
        },
    )

    with pytest.raises(ValueError, match="execution_status"):
        AssessmentRunValidator.validate(assessment_run)


def test_reject_invalid_finding_classification(
    assessment_run_factory,
    policy_execution_record_factory,
    finding_factory,
):
    """Reject findings with unsupported classifications."""

    finding = finding_factory(classification="critical")

    assessment_run = assessment_run_factory(
        assessments={
            "A1": policy_execution_record_factory(
                policy_id="A1",
                findings=[finding],
            ),
        },
    )

    with pytest.raises(ValueError, match="invalid classification"):
        AssessmentRunValidator.validate(assessment_run)


def test_reject_finding_policy_identifier_mismatch(
    assessment_run_factory,
    policy_execution_record_factory,
    finding_factory,
):
    """Ensure findings belong to their containing policy."""

    finding = finding_factory(policy_id="A2")

    assessment_run = assessment_run_factory(
        assessments={
            "A1": policy_execution_record_factory(
                policy_id="A1",
                findings=[finding],
            ),
        },
    )

    with pytest.raises(ValueError, match="policy identifier mismatch"):
        AssessmentRunValidator.validate(assessment_run)


def test_reject_invalid_evidence_references(
    assessment_run_factory,
    policy_execution_record_factory,
    finding_factory,
):
    """Reject empty or non-string evidence references."""

    finding = finding_factory()
    finding["evidence_references"] = ["tls_version", ""]

    assessment_run = assessment_run_factory(
        assessments={
            "A1": policy_execution_record_factory(
                policy_id="A1",
                findings=[finding],
            ),
        },
    )

    with pytest.raises(ValueError, match="evidence_references"):
        AssessmentRunValidator.validate(assessment_run)


def test_reject_missing_policy_metadata(
    assessment_run_factory,
    policy_execution_record_factory,
):
    """Reject policy execution records without metadata."""

    record = policy_execution_record_factory(policy_id="A1")
    record.pop("metadata")

    assessment_run = assessment_run_factory(
        assessments={"A1": record},
    )

    with pytest.raises(ValueError, match="metadata"):
        AssessmentRunValidator.validate(assessment_run)


def test_reject_policy_metadata_identifier_mismatch(
    assessment_run_factory,
    policy_execution_record_factory,
    policy_metadata_factory,
):
    """Ensure metadata identifiers match their assessment keys."""

    record = policy_execution_record_factory(
        policy_id="A1",
        metadata=policy_metadata_factory(policy_id="A2"),
    )

    assessment_run = assessment_run_factory(
        assessments={"A1": record},
    )

    with pytest.raises(ValueError, match="identifier mismatch"):
        AssessmentRunValidator.validate(assessment_run)


def test_reject_policy_metadata_without_rules(
    assessment_run_factory,
    policy_execution_record_factory,
    policy_metadata_factory,
):
    """Reject policy metadata without its required rule definitions."""

    metadata = policy_metadata_factory(rules=[])

    record = policy_execution_record_factory(
        policy_id="A1",
        metadata=metadata,
    )

    assessment_run = assessment_run_factory(
        assessments={"A1": record},
    )

    with pytest.raises(ValueError, match="rules"):
        AssessmentRunValidator.validate(assessment_run)
