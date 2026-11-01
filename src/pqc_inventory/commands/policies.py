"""CLI command for listing registered assessment policies."""

import argparse

from pqc_inventory.assessment.policy_setup import create_default_registry

from pqc_inventory.commands.constants import EXIT_SUCCESS


def list_policies() -> int:
    """Display the policies registered in the application."""
    registry = create_default_registry()
    policies = registry.all()

    if not policies:
        print("No assessment policies are registered.")
        return EXIT_SUCCESS

    print()
    print("Registered Assessment Policies")
    print("===============================")
    print()

    for policy in policies:
        print(f"ID:          {policy.policy_id}")
        print(f"Name:        {policy.policy_name}")
        print(f"Version:     {policy.policy_version}")
        print(f"Description: {policy.policy_description}")
        print()

    print(f"Total policies: {len(policies)}")
    print()
    return EXIT_SUCCESS


def run_policies(args: argparse.Namespace) -> int:
    """Execute the policies command."""
    return list_policies()


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the policies command."""

    subparsers.add_parser(
        "policies",
        help="List registered assessment policies.",
        description="Display the assessment policies available in the application.",
    )
