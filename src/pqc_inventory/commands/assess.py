"""CLI command for assessing collected TLS evidence."""

import argparse
import sys
from pathlib import Path

from pqc_inventory.assessment.interfaces import AssessmentPolicy
from pqc_inventory.assessment.models import AssessmentRun
from pqc_inventory.assessment.policy_setup import create_default_registry
from pqc_inventory.application.assessment_service import AssessmentService
from pqc_inventory.commands.common import resolve_command_output_path
from pqc_inventory.commands.constants import (
    EXIT_CANCELLED,
    EXIT_ERROR,
    EXIT_INVALID_INPUT,
    EXIT_PARTIAL,
    EXIT_SUCCESS,
)
from pqc_inventory.storage.json_repository import JSONRepositoryError


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the assessment command and its arguments."""

    assess_parser = subparsers.add_parser(
        "assess",
        help="Assess previously collected TLS evidence.",
        description="Evaluate saved TLS evidence using assessment policies.",
    )

    assess_parser.add_argument(
        "--input",
        required=True,
        help="Path to the saved TLS evidence JSON file.",
    )

    assess_parser.add_argument(
        "--output",
        default="data/assessments/assessment_runs.json",
        help=(
            "Path where assessment results will be saved "
            "(default: data/assessments/assessment_runs.json)."
        ),
    )

    assess_parser.add_argument(
        "--policies",
        nargs="+",
        dest="policies",
        metavar="POLICY_ID",
        help=(
            "Policy IDs to execute (e.g., --policies A1 A2). "
            "If omitted, all registered policies are considered."
        ),
    )

    assess_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation and execute all registered policies.",
    )


def get_registered_policies() -> tuple[AssessmentPolicy, ...]:
    """Retrieve all policies registered in the application."""
    return create_default_registry().all()


def confirm_all_policies(policies: tuple[AssessmentPolicy, ...]) -> bool:
    """Display registered policies and confirm their execution."""

    print("\nThe following assessment policies will be executed:\n")

    for policy in policies:
        print(f"  {policy.policy_id} - {policy.policy_name}")

    print(f"\nTotal policies: {len(policies)}")

    response = input("\nExecute all registered policies? [y/N]: ").strip().lower()

    return response in {"y", "yes"}


def resolve_policy_selection(
    args: argparse.Namespace,
) -> list[str] | None:
    """Resolve which assessment policies should be executed."""
    policies = get_registered_policies()

    if not policies:
        raise ValueError("No assessment policies are registered.")

    registered_ids = [policy.policy_id for policy in policies]

    # Case 1: Explicit policy selection
    if args.policies is not None:
        selected_ids = args.policies

        if not selected_ids:
            raise ValueError("At least one assessment policy must be selected.")

        if len(selected_ids) != len(set(selected_ids)):
            raise ValueError("Duplicate policy IDs were supplied.")

        unknown_ids = [
            policy_id for policy_id in selected_ids if policy_id not in registered_ids
        ]

        if unknown_ids:
            raise ValueError(f"Unregistered policy IDs: {', '.join(unknown_ids)}")

        return selected_ids

    # Case 2: Execute all policies without confirmation.
    if args.yes:
        return registered_ids

    # Case 3: Interactive confirmation.
    if not sys.stdin.isatty():
        raise ValueError(
            "Policy selection is required in non-interactive mode. "
            "Specify --policies or --yes."
        )

    if confirm_all_policies(policies):
        return registered_ids

    # Case 4: User declines execution.
    return None


def execute_assessment(
    input_path: Path,
    output_path: Path,
    policy_ids: list[str],
) -> list[AssessmentRun]:
    """Execute assessment policies against collected TLS evidence.

    Args:
        input_path: Path to the collected TLS evidence.
        output_path: Destination for the assessment results.
        policy_ids: Assessment policies selected for execution.

    Returns:
        Assessment runs produced by the assessment service.
    """

    service = AssessmentService()

    return service.assess_file(
        input_path=input_path,
        output_path=output_path,
        policy_ids=policy_ids,
    )


def summarize_assessment_results(
    results: list[AssessmentRun],
    output_path: Path,
) -> int:
    """Display assessment statistics and determine the operation's exit code."""

    status_counts = {
        "completed": 0,
        "partial": 0,
        "failed": 0,
        "not_assessed": 0,
    }

    for result in results:
        for policy_record in result["assessments"].values():
            status = policy_record["result"]["execution_status"]
            status_counts[status] += 1

    total = sum(status_counts.values())

    print("\nAssessment Summary")
    print("------------------")
    print(f"Targets assessed:       {len(results)}")
    print(f"Policy executions:      {total}")
    print()
    print(f"Completed:              {status_counts['completed']}")
    print(f"Partial:                {status_counts['partial']}")
    print(f"Failed:                 {status_counts['failed']}")
    print(f"Not assessed:           {status_counts['not_assessed']}")
    print()
    print(f"Assessment results saved: {output_path}")

    if any(
        status_counts[status] > 0 for status in ("partial", "failed", "not_assessed")
    ):
        return EXIT_PARTIAL

    return EXIT_SUCCESS


def run_assess(  # pylint: disable=too-many-return-statements
    args: argparse.Namespace,
) -> int:
    """Execute the assessment workflow and report its outcome."""

    # Step 1: Resolve the assessment policies to execute.
    try:
        selected_policy_ids = resolve_policy_selection(args)
    except ValueError as exc:
        print(f"Policy selection error: {exc}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    except (EOFError, KeyboardInterrupt):
        print("\nAssessment cancelled by user.")
        return EXIT_CANCELLED

    if selected_policy_ids is None:
        print("Assessment cancelled by user.")
        return EXIT_CANCELLED

    # Step 2: Approve the output destination path.
    output_path = resolve_command_output_path(
        output_path=args.output,
        allowed_extensions={".json"},
    )

    if output_path is None:
        print("Assessment cancelled by user.")
        return EXIT_CANCELLED

    # Step 3: Execute the assessment.
    try:
        results = execute_assessment(
            input_path=Path(args.input),
            output_path=output_path,
            policy_ids=selected_policy_ids,
        )
    except ValueError as exc:
        print(f"Assessment input error: {exc}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    except (JSONRepositoryError, KeyError) as exc:
        print(f"Assessment error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    # Step 4: Summarize the assessment results.
    return summarize_assessment_results(results, output_path)
