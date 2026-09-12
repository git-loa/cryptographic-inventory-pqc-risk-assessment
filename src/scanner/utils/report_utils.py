"""
Utility functions for building combined security reports.
"""

from datetime import datetime, timedelta

from src.scanner.models import TLSScanResult, PQCScore, CombinedTLSReport


def _safe_is_expiring(date_str: str, soon: datetime) -> bool:

    try:
        return datetime.fromisoformat(date_str) < soon
    except (TypeError, ValueError):
        return False


def build_combined_reports(
    tls_results: list[TLSScanResult],
    pqc_scores: list[PQCScore],
) -> list[CombinedTLSReport]:
    """
    Merge TLS and PQC results into unified CombinedTLSReport objects.
    Parameters:
        tls_results: List of TLSScanResult dictionaries.
        pqc_scores: List of PQCScore dictionaries.
    Returns:
        List of CombinedTLSReport dictionaries, each containing:
        - domain: The scanned domain.
        - tls: The TLS scan result.
        - pqc: The PQC score.
    """
    combined: list[CombinedTLSReport] = []

    # We assume TLS and PQC lists align by domain order.
    for tls, pqc in zip(tls_results, pqc_scores):
        combined.append(
            {
                "domain": tls["domain"],
                "tls": tls,
                "pqc": pqc,
            }
        )

    return combined


def compute_top_findings(
    reports: list[CombinedTLSReport],
) -> dict[str, list[str] | int]:
    """
    Compute top findings from combined TLS + PQC reports.
    Returns a dictionary summarizing the findings.

    The findings include:
    - Total domains scanned
    - Domains with TLS errors
    - Domains with PQC errors
    - Domains with high PQC risk
    - Domains using deprecated TLS versions
    - Domains with weak RSA/ECC keys
    - Domains with certificates expiring within 30 days

    Parameters:
        reports: List of CombinedTLSReport dictionaries.
    Returns:
        Dictionary summarizing the top findings.
    """
    findings: dict[str, list[str] | int] = {}

    findings["total_domains"] = len(reports)

    # TLS errors
    findings["tls_errors"] = [r["domain"] for r in reports if r["tls"].get("error")]

    # PQC errors
    findings["pqc_errors"] = [r["domain"] for r in reports if r["pqc"].get("error")]

    findings["tls_successes"] = findings["total_domains"] - len(findings["tls_errors"])
    findings["pqc_successes"] = findings["total_domains"] - len(findings["pqc_errors"])

    # High PQC risk
    findings["high_risk"] = [
        r["domain"] for r in reports if r["pqc"]["pqc_risk"] == "High"
    ]

    # Deprecated TLS versions
    deprecated = {"TLSv1", "TLSv1.1", "SSLv3", "SSLv2"}
    findings["deprecated_tls"] = [
        r["domain"] for r in reports if r["tls"].get("tls_version") in deprecated
    ]

    # Weak RSA/ECC keys
    findings["weak_keys"] = [
        r["domain"]
        for r in reports
        if r["tls"].get("key_size") and r["tls"].get("key_size") < 2048
    ]

    # Certificates expiring soon
    soon = datetime.now() + timedelta(days=30)
    findings["expiring_certs"] = [
        r["domain"]
        for r in reports
        if r["tls"].get("not_after") and _safe_is_expiring(r["tls"]["not_after"], soon)
    ]

    return findings
