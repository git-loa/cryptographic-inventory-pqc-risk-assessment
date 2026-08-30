"""
JSON Persistence Layer for TLS and PQC Results.

Provides helper functions for saving and loading TLS scan results and PQC
scoring results. Includes validation to ensure JSON structure integrity.
"""

import json
from pathlib import Path
from typing import Any

from src.scanner.utils.logger import get_logger
from src.scanner.models import TLSScanResult, PQCScore

logger = get_logger(__name__)


# -----------------------------
# TLS JSON Save / Load
# -----------------------------


def save_tls_results(
    results: list[TLSScanResult],
    path: str | Path = "data/processed/tls_results.json",
) -> None:
    """Save TLS scan results to JSON.

    Parameters
    ----------
    results : list[TLSScanResult]
        The TLS scan results to save.
    path : str | Path, optional
        The path to the JSON file where results will be saved,
        by default "data/processed/tls_results.json".
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    logger.info("Saving TLS results to %s", path)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info("TLS results saved successfully.")


def _validate_tls_entry(entry: dict[str, Any]) -> None:
    """Validate a single TLSScanResult entry.

    Raises ValueError if required fields are missing.

    Parameters
    ----------
    entry : dict[str, Any]
        The TLS scan result entry to validate.
    """
    required_fields = ["domain", "port"]

    for field in required_fields:
        if field not in entry:
            raise ValueError(f"Invalid TLS entry: missing required field '{field}'")

    # If no error, validate TLS fields
    if "error" not in entry:
        tls_fields = [
            "tls_version",
            "cipher_suite",
            "cipher_strength",
            "key_size",
            "not_before",
            "not_after",
            "certificate_issuer",
            "certificate_subject",
        ]
        for field in tls_fields:
            if field not in entry:
                raise ValueError(
                    f"Invalid TLS entry for domain '{entry.get('domain')}': "
                    f"missing TLS field '{field}'"
                )

        # Structural validation
        if not isinstance(entry["certificate_subject"], dict):
            raise ValueError("Invalid TLS entry: 'certificate_subject' must be a dict")

        if not isinstance(entry["certificate_issuer"], dict):
            raise ValueError("Invalid TLS entry: 'certificate_issuer' must be a dict")


def load_tls_results(
    path: str | Path = "data/processed/tls_results.json",
) -> list[TLSScanResult]:
    """Load and validate TLS scan results from JSON.

    Parameters
    ----------
    path : str | Path, optional
        The path to the JSON file containing TLS results,
        by default "data/processed/tls_results.json".

    Returns
    -------
    list[TLSScanResult]
        The loaded and validated TLS scan results.
    """
    logger.info("Loading TLS results from %s", path)

    if not Path(path).exists():
        raise FileNotFoundError(f"TLS results file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("TLS results JSON must be a list of TLSScanResult objects")

    for entry in data:
        if not isinstance(entry, dict):
            raise ValueError("TLS results must contain dictionaries")
        _validate_tls_entry(entry)

    logger.info("TLS results loaded and validated successfully.")
    return data


# -----------------------------
# PQC JSON Save / Load
# -----------------------------


def save_pqc_scores(
    scores: list[PQCScore],
    path: str | Path = "data/processed/pqc_scores.json",
) -> None:
    """Save PQC scoring results to JSON.

    Parameters
    ----------
    scores : list[PQCScore]
        The PQC scoring results to save.
    path : str | Path, optional
        The path to the JSON file where results will be saved,
        by default "data/processed/pqc_scores.json".
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    logger.info("Saving PQC scores to %s", path)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2)

    logger.info("PQC scores saved successfully.")


def _validate_pqc_entry(entry: dict[str, Any]) -> None:
    """Validate a single PQCScore entry.

    Raises ValueError if required fields are missing.

    Parameters
    ----------
    entry : dict[str, Any]
        The PQC score entry to validate.
    """
    required_fields = [
        "domain",
        "tls_score",
        "pqc_risk",
        "reasons",
    ]

    # Validate required fields
    for field in required_fields:
        if field not in entry:
            raise ValueError(f"Invalid PQC entry: missing required field '{field}'")

    # Validate types of specific fields
    if not isinstance(entry["domain"], str):
        raise ValueError("Invalid PQC entry: 'domain' must be a string")

    if not isinstance(entry["reasons"], list):
        raise ValueError("Invalid PQC entry: 'reasons' must be a list")

    if not isinstance(entry["pqc_risk"], str):
        raise ValueError("Invalid PQC entry: 'pqc_risk' must be a string")

    if not isinstance(entry["tls_score"], int):
        raise ValueError("Invalid PQC entry: 'tls_score' must be an integer")


def load_pqc_scores(
    path: str | Path = "data/processed/pqc_scores.json",
) -> list[PQCScore]:
    """Load and validate PQC scoring results from JSON.

    Parameters
    ----------
    path : str | Path, optional
        The path to the JSON file containing PQC scores,
        by default "data/processed/pqc_scores.json".

    Returns
    -------
    list[PQCScore]
        The loaded and validated PQC scoring results.
    """
    logger.info("Loading PQC scores from %s", path)

    if not Path(path).exists():
        raise FileNotFoundError(f"PQC scores file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("PQC scores JSON must be a list of PQCScore objects")

    for entry in data:
        if not isinstance(entry, dict):
            raise ValueError("PQC scores must contain dictionaries")
        _validate_pqc_entry(entry)

    logger.info("PQC scores loaded and validated successfully.")
    return data
