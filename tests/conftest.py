"""
Unified pytest fixtures for the TLS + PQC pipeline.
Covers:
- domain loading
- TLS results
- PQC scores
- combined report data
- markdown-ready report data
"""

import pytest

from src.scanner.domain_loader import load_domains
from src.scanner.json_io import load_tls_results, load_pqc_scores
from src.scanner.combined_report import build_combined_reports

# ---------------------------------------------------------
# DOMAIN FIXTURES
# ---------------------------------------------------------


@pytest.fixture
def domains_builtin():
    """Built-in sample domains used across tests."""
    return ["example.com", "google.com"]


@pytest.fixture
def domains_testfile():
    """Domains loaded from tests/test_domains.txt if present."""
    try:
        return load_domains("tests/test_domains.txt")
    except FileNotFoundError:
        return []


# pylint: disable=redefined-outer-name
@pytest.fixture
def all_domains(domains_builtin, domains_testfile):
    """
    Comprehensive domain fixture combining:
    - built-in domains
    - test file domains
    - future domain sources (extendable)
    """
    combined = set(domains_builtin) | set(domains_testfile)
    return sorted(combined)


# ---------------------------------------------------------
# TLS + PQC FIXTURES
# ---------------------------------------------------------


@pytest.fixture
def tls_results():
    """TLS scan results loaded from JSON."""
    return load_tls_results()


@pytest.fixture
def pqc_scores():
    """PQC scores loaded from JSON."""
    return load_pqc_scores()


# ---------------------------------------------------------
# COMBINED REPORT FIXTURE
# ---------------------------------------------------------


@pytest.fixture
def combined_report(tls_results, pqc_scores):
    """Combined TLS + PQC report used by multiple modules."""
    return build_combined_reports(tls_results, pqc_scores)


# ---------------------------------------------------------
# MARKDOWN INPUT FIXTURE
# ---------------------------------------------------------


@pytest.fixture
def markdown_input(combined_report):
    """
    Markdown-ready data structure.
    Useful for testing markdown_report.render_markdown().
    """
    return {
        "data": combined_report,
        "author": "Leonard",
        "organization": "Quantum Security",
    }
