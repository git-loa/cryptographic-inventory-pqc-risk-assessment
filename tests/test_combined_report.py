"""Ensure assessment produces deterministic output."""

from src.scanner.assessment import assess_tls_results


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


def test_combined_report_domain_alignment(tls_results):
    """Ensure each combined entry preserves its TLS result and score association."""
    pqc_scores, combined = assess_tls_results(tls_results)

    assert len(combined) == len(tls_results)
    assert len(pqc_scores) == len(tls_results)
    for tls, score, report in zip(tls_results, pqc_scores, combined):
        assert report["domain"] == tls["domain"]
        assert report["tls"] == tls
        assert report["pqc"] == score


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
            # Failed scans must not report successful TLS metadata.
            assert tls["tls_version"] is None
            assert tls["cipher_suite"] is None
            assert tls["cipher_strength"] is None
            assert tls["key_size"] is None
            assert tls["public_key_algorithm"] is None
            assert tls["certificate_subject"] == {}
            assert tls["certificate_issuer"] == {}
            assert tls["not_before"] is None
            assert tls["not_after"] is None
        else:
            # Successful TLS entries must contain required fields
            assert "tls_version" in tls
            assert "cipher_suite" in tls
            assert "key_size" in tls
            assert "public_key_algorithm" in tls
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


def test_combined_report_roundtrip(tls_results):
    """
    Ensure build_combined_reports produces deterministic output.
    """
    _, combined_1 = assess_tls_results(tls_results)
    _, combined_2 = assess_tls_results(tls_results)

    assert combined_1 == combined_2
