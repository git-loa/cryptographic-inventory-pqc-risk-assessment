"""Define request models for assessment report generation."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReportRequest:
    """Define the inputs required to generate an assessment report."""

    input_path: Path
    output_path: Path
    author: str
    organization: str
    report_format: str = "markdown"


@dataclass(frozen=True)
class BatchReportRequest:
    """Define the inputs required to generate all assessment reports."""

    input_path: Path
    output_directory: Path
    author: str
    organization: str
