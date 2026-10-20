"""
JSON persistence for TLS scan results and combined A1 assessment reports.

Provides JSON serialization, loading, and structural validation for
data exchanged between the scanning, assessment, and reporting stages.
"""

import json
from pathlib import Path
from typing import Any

from src.scanner.models import CombinedTLSReport, TLSScanResult
from src.scanner.utils.logger import get_logger

logger = get_logger(__name__)

A1_DIMENSIONS = {
    "tls_version",
    "cipher_suite",
    "public_key_algorithm",
    "certificate_signature",
}

A1_CLASSIFICATIONS = {
    "acceptable",
    "acceptable_with_review",
    "unacceptable",
    "unknown",
}


# ---------------------------------------------------------
# TLS scan results
# ---------------------------------------------------------


def save_tls_results(
    results: list[TLSScanResult],
    path: str | Path = "data/processed/tls_results.json",
) -> None:
    """Save TLS scan results to a JSON file."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Saving TLS results to %s", output_path)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=2)

    logger.info("TLS results saved successfully.")


def _validate_tls_entry(entry: dict[str, Any]) -> None:
    """Validate the required structure of one TLS scan result."""
    for field in ("domain", "port"):
        if field not in entry:
            raise ValueError(f"Invalid TLS entry: missing required field '{field}'")

    if not isinstance(entry["domain"], str) or not entry["domain"].strip():
        raise ValueError("Invalid TLS entry: 'domain' must be a non-empty string")

    if not isinstance(entry["port"], int) or isinstance(entry["port"], bool):
        raise ValueError("Invalid TLS entry: 'port' must be an integer")

    # Failed scans may not contain successful TLS or certificate metadata.
    if "error" in entry:
        return

    required_fields = (
        "tls_version",
        "cipher_suite",
        "cipher_strength",
        "key_size",
        "public_key_algorithm",
        "not_before",
        "not_after",
        "certificate_issuer",
        "certificate_subject",
    )

    for field in required_fields:
        if field not in entry:
            raise ValueError(
                f"Invalid TLS entry for domain '{entry['domain']}': "
                f"missing TLS field '{field}'"
            )

    for field in ("certificate_subject", "certificate_issuer"):
        if not isinstance(entry[field], dict):
            raise ValueError(f"Invalid TLS entry: '{field}' must be a dictionary")

    algorithm = entry["public_key_algorithm"]
    if algorithm is not None and not isinstance(algorithm, str):
        raise ValueError(
            "Invalid TLS entry: 'public_key_algorithm' must be a string or None"
        )


def load_tls_results(
    path: str | Path = "data/processed/tls_results.json",
) -> list[TLSScanResult]:
    """Load and validate TLS scan results from JSON."""
    input_path = Path(path)
    logger.info("Loading TLS results from %s", input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"TLS results file not found: {input_path}")

    with input_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("TLS results JSON must contain a list")

    for entry in data:
        if not isinstance(entry, dict):
            raise ValueError("TLS results must contain JSON objects")

        _validate_tls_entry(entry)

    logger.info("TLS results loaded and validated successfully.")
    return data


# ---------------------------------------------------------
# A1 finding validation
# ---------------------------------------------------------


def _validate_a1_finding(
    dimension: str,
    finding: Any,
    domain: str,
) -> None:
    """Validate one A1 finding and its required fields."""
    if not isinstance(finding, dict):
        raise ValueError(
            f"Invalid A1 assessment for '{domain}': " f"'{dimension}' must be an object"
        )

    required_fields = ("dimension", "observed", "classification", "reason")

    for field in required_fields:
        if field not in finding:
            raise ValueError(
                f"Invalid A1 finding '{dimension}' for '{domain}': "
                f"missing required field '{field}'"
            )

    if finding["dimension"] != dimension:
        raise ValueError(
            f"Invalid A1 finding for '{domain}': " f"expected dimension '{dimension}'"
        )

    for field in ("dimension", "observed", "classification", "reason"):
        if not isinstance(finding[field], str):
            raise ValueError(
                f"Invalid A1 finding '{dimension}' for '{domain}': "
                f"'{field}' must be a string"
            )

    if finding["classification"] not in A1_CLASSIFICATIONS:
        raise ValueError(
            f"Invalid A1 classification for '{domain}' in '{dimension}': "
            f"{finding['classification']!r}"
        )


def _validate_a1_assessment(
    assessment: Any,
    domain: str,
) -> None:
    """Validate all four required A1 assessment dimensions."""
    if not isinstance(assessment, dict):
        raise ValueError(
            f"Invalid combined report for '{domain}': " "'a1' must be an object"
        )

    for dimension in A1_DIMENSIONS:
        if dimension not in assessment:
            raise ValueError(
                f"Invalid A1 assessment for '{domain}': "
                f"missing required dimension '{dimension}'"
            )

        _validate_a1_finding(
            dimension=dimension,
            finding=assessment[dimension],
            domain=domain,
        )


# ---------------------------------------------------------
# Combined A1 assessment reports
# ---------------------------------------------------------


def load_combined_reports(
    path: str | Path = "reports/combined_report.json",
) -> list[CombinedTLSReport]:
    """Load and validate combined TLS evidence and A1 findings."""
    input_path = Path(path)
    logger.info("Loading combined reports from %s", input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Combined report file not found: {input_path}")

    with input_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Combined report JSON must contain a list")

    for entry in data:
        if not isinstance(entry, dict):
            raise ValueError("Combined reports must contain JSON objects")

        for field in ("domain", "tls", "a1"):
            if field not in entry:
                raise ValueError(
                    "Invalid combined report: " f"missing required field '{field}'"
                )

        domain = entry["domain"]
        tls = entry["tls"]

        if not isinstance(domain, str) or not domain.strip():
            raise ValueError(
                "Invalid combined report: 'domain' must be a non-empty string"
            )

        if not isinstance(tls, dict):
            raise ValueError(
                f"Invalid combined report for '{domain}': " "'tls' must be an object"
            )

        if tls.get("domain") != domain:
            raise ValueError(
                f"Invalid combined report for '{domain}': "
                "report domain does not match TLS evidence domain"
            )

        _validate_a1_assessment(entry["a1"], domain)

    logger.info("Combined reports loaded and validated successfully.")
    return data
