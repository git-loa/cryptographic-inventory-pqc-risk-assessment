"""
Utilities for summarizing TLS inventory and A1 assessment findings.
"""

from collections import Counter
from typing import Any

from src.scanner.models import CombinedTLSReport

A1_CLASSIFICATIONS = (
    "acceptable",
    "acceptable_with_review",
    "unacceptable",
    "unknown",
)

A1_DIMENSION_LABELS = {
    "tls_version": "TLS version",
    "cipher_suite": "Cipher suite",
    "public_key_algorithm": "Certificate public-key algorithm",
    "certificate_signature": "Certificate signature algorithm",
}


def compute_top_findings(
    reports: list[CombinedTLSReport],
) -> dict[str, Any]:
    """
    Summarize scan outcomes and A1 findings without producing a risk score.

    Counts are calculated per assessment finding, not per domain.
    A single domain can therefore contribute multiple findings.

    Args:
        reports: Combined TLS evidence and A1 assessment reports.

    Returns:
        Summary statistics and lists of findings grouped by classification.
    """
    classification_counts: Counter[str] = Counter(
        {classification: 0 for classification in A1_CLASSIFICATIONS}
    )

    findings_by_classification: dict[str, list[dict[str, str]]] = {
        classification: [] for classification in A1_CLASSIFICATIONS
    }

    tls_errors: list[dict[str, str]] = []

    for report in reports:
        domain = report["domain"]
        tls_result = report["tls"]

        if tls_result.get("error"):
            tls_errors.append(
                {
                    "domain": domain,
                    "error": str(tls_result["error"]),
                }
            )

        for dimension, finding in report["a1"].items():
            classification = finding["classification"]

            classification_counts[classification] += 1

            finding_summary = {
                "domain": domain,
                "dimension": A1_DIMENSION_LABELS.get(dimension, dimension),
                "observed": finding["observed"],
                "classification": classification,
                "reason": finding["reason"],
            }

            findings_by_classification[classification].append(finding_summary)

    total_findings = sum(classification_counts.values())
    tls_error_count = len(tls_errors)

    return {
        "total_domains": len(reports),
        "tls_successes": len(reports) - tls_error_count,
        "tls_errors": tls_errors,
        "total_findings": total_findings,
        "classification_counts": dict(classification_counts),
        "unacceptable_findings": findings_by_classification["unacceptable"],
        "review_findings": findings_by_classification["acceptable_with_review"],
        "unknown_findings": findings_by_classification["unknown"],
    }
