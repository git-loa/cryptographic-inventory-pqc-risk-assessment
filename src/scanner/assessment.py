"""
Assessment orchestration for the TLS inventory pipeline.

Coordinates the A1 TLS configuration assessment and combines
its findings with the original TLS scan evidence.
"""

from src.scanner.models import (
    CombinedTLSReport,
    TLSScanResult,
)
from src.scanner.a1_assessment import assess_a1_configuration


def assess_tls_results(
    tls_results: list[TLSScanResult],
) -> list[CombinedTLSReport]:
    """
    Assess TLS scan results using A1.

    Each input scan is assessed independently. The original scan
    evidence and the resulting A1 findings are preserved together.

    No numerical risk score is calculated.

    Args:
        tls_results: TLS scan results collected by the scanner.

    Returns:
        Combined reports containing TLS evidence and A1 findings.
        The order of the input scan results is preserved.

    """

    combined_reports: list[CombinedTLSReport] = []

    for tls_result in tls_results:
        # Assess A1 dimensions independently; do not collapse them into a score.
        a1_assessment = assess_a1_configuration(tls_result)

        combined_reports.append(
            {
                "domain": tls_result["domain"],
                "tls": tls_result,
                "a1": a1_assessment,
            }
        )

    return combined_reports
