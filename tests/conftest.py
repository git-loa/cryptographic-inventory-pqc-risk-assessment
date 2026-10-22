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
