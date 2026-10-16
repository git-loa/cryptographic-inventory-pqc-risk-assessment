"""
TLS and PQC Assessment Orchestration.

Calculates PQC scores from TLS scan results and constructs
combined records without requiring a separate matching step.
"""

from src.scanner.models import (
    CombinedTLSReport,
    PQCScore,
    TLSScanResult,
)

from src.scanner.pqc_assessment import assess_pqc_exposure
from src.scanner.pqc_scoring import score_pqc


def assess_tls_results(
    tls_results: list[TLSScanResult],
) -> tuple[list[PQCScore], list[CombinedTLSReport]]:
    """
    Calculate PQC scores and construct combined reports.
    Each score is calculated directly from its corresponding TLS result.
    The original TLS result order is preserved.

    Parameters:
        tls_results: TLS scan results to assess.

    Returns:
        A tuple containing:
        - The list of PQC scores.
        - The list of combined TLS and PQC reports.
    """

    pqc_scores: list[PQCScore] = []
    combined_reports: list[CombinedTLSReport] = []

    for tls_result in tls_results:
        # Preserve the existing heuristic scoring behavior.
        pqc_score = score_pqc(tls_result)
        pqc_scores.append(pqc_score)

        # Assess key-establishment exposure independently.
        pqc_exposure = assess_pqc_exposure(tls_result)

        # Combine the original scan evidence and both assessments.
        combined_reports.append(
            {
                "domain": tls_result["domain"],
                "tls": tls_result,
                "pqc": pqc_score,
                "pqc_exposure": pqc_exposure,
            }
        )

    return pqc_scores, combined_reports
