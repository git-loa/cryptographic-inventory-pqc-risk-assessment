"""
Unit tests for the combined TLS + PQC report builder.
"""

from src.scanner.combined_report import build_combined_reports


def test_combined_report_structure(combined_report):
    """
    Ensure the combined report is a list of merged TLS + PQC entries.
    """
    assert isinstance(combined_report, list)
    assert len(combined_report) > 0

    first = combined_report[0]
    assert isinstance(first, dict)
    assert "domain" in first
    assert "tls" in first
    assert "pqc" in first


def test_combined_report_domain_alignment(tls_results, pqc_scores):
    """
    Ensure each combined entry aligns TLS and PQC data by domain.
    """
    combined = build_combined_reports(tls_results, pqc_scores)

    tls_domains = [entry["domain"] for entry in tls_results]
    pqc_domains = [entry["domain"] for entry in pqc_scores]

    for entry in combined:
        assert entry["domain"] in tls_domains
        assert entry["domain"] in pqc_domains


def test_combined_report_tls_section(combined_report):
    """
    Ensure TLS section contains either full TLS metadata or an error entry.
    """
    for entry in combined_report:
        tls = entry["tls"]
        assert isinstance(tls, dict)
        assert "domain" in tls
        assert "port" in tls

        if "error" in tls:
            # Error entries must not contain TLS metadata
            assert "tls_version" not in tls
            assert "cipher_suite" not in tls
            assert "key_size" not in tls
        else:
            # Successful TLS entries must contain required fields
            assert "tls_version" in tls
            assert "cipher_suite" in tls
            assert "key_size" in tls
            assert "certificate_subject" in tls
            assert "certificate_issuer" in tls
            assert "not_before" in tls
            assert "not_after" in tls


def test_combined_report_pqc_section(combined_report):
    """
    Ensure PQC section contains correct PQC scoring fields.
    """
    for entry in combined_report:
        pqc = entry["pqc"]
        assert isinstance(pqc, dict)

        assert "domain" in pqc
        assert "tls_score" in pqc
        assert "pqc_risk" in pqc
        assert "reasons" in pqc
        assert isinstance(pqc["reasons"], list)


def test_combined_report_roundtrip(tls_results, pqc_scores):
    """
    Ensure build_combined_reports produces deterministic output.
    """
    combined_1 = build_combined_reports(tls_results, pqc_scores)
    combined_2 = build_combined_reports(tls_results, pqc_scores)

    assert combined_1 == combined_2
