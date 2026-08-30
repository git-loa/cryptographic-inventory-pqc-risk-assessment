"""
Score PQC from saved TLS JSON

This module loads TLS scan results from data/processed/tls_results.json,
computes PQC scores for each domain, and saves the results to
data/processed/pqc_scores.json.

It allows offline scoring, batch scoring, and dashboard integration.
"""

from __future__ import annotations

from src.scanner.json_io import load_tls_results, save_pqc_scores
from src.scanner.pqc_scoring import score_pqc
from src.scanner.models import PQCScore, TLSScanResult


def score_all_tls_results() -> list[PQCScore]:
    """
    Load TLS results from JSON, compute PQC scores, and return them.
    """
    tls_results: list[TLSScanResult] = load_tls_results()
    pqc_scores: list[PQCScore] = [score_pqc(result) for result in tls_results]
    return pqc_scores


def main() -> None:
    """
    Score all TLS results and save PQC scores to JSON.
    """
    pqc_scores = score_all_tls_results()
    save_pqc_scores(pqc_scores)

    print("PQC scoring complete.")
    print("Saved to data/processed/pqc_scores.json")


if __name__ == "__main__":
    main()
