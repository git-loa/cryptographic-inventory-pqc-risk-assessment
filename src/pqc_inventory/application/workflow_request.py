"""Define request models for complete TLS assessment workflows."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkflowOutputPaths:
    """Define the output destinations for workflow artifacts."""

    evidence: Path
    assessment: Path
    report: Path


@dataclass(frozen=True)
class WorkflowRequest:
    """Define the inputs required to execute the complete workflow.

    Attributes:
        targets: Validated TLS endpoint names or IP addresses.
        output_paths: Destinations for the workflow artifacts.
        port: TCP port used for TLS connections.
        policy_ids: Assessment policies to execute. None selects all.
        author: Name of the report author.
        organization: Organization associated with the report.
    """

    targets: tuple[str, ...]
    output_paths: WorkflowOutputPaths

    port: int = 443
    policy_ids: tuple[str, ...] | None = None

    author: str = "Unknown Author"
    organization: str = "Independent Research"
