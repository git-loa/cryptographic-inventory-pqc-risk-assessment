"""
Fuzz tests for the TLS scanner.
These tests verify that scan_domain() behaves safely and predictably
under a wide range of malformed, extreme, and valid domain inputs.
"""

from hypothesis import given, strategies as st, settings
from src.scanner.tls_scanner import scan_domain

# ------------------------------------------------------------
# Domain fuzzing strategies
# ------------------------------------------------------------

# Random bytes → decoded with errors ignored
random_bytes = st.binary(min_size=0, max_size=200).map(
    lambda b: b.decode("utf-8", errors="ignore")
)

# Valid-ish domain patterns (loose but realistic)
valid_domain_like = st.from_regex(
    r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    fullmatch=True,
).filter(lambda s: len(s) <= 253)

# Invalid domain patterns (realistic malformed cases)
invalid_domain_like = st.sampled_from(
    [
        ".example.com",
        "example..com",
        "exa mple.com",
        "example!.com",
        "-example.com",
        "example-.com",
        "example",
        "",
    ]
)

# Realistic domain samples
sample_domains = st.sampled_from(
    [
        "example.com",
        "google.com",
        "localhost",
        "invalid.invalid",
        "test",
        "a" * 250 + ".com",
        "xn--d1acufc.xn--p1ai",
        "mañana.com",
        "😀.com",
    ]
)

# Combined strategy (no redundancy)
domain_strategy = st.one_of(
    st.text(min_size=0, max_size=200),
    random_bytes,
    valid_domain_like,
    invalid_domain_like,
    sample_domains,
)

# ------------------------------------------------------------
# Fuzz Test
# ------------------------------------------------------------


@settings(deadline=None, max_examples=200)
@given(domain_strategy)
def test_scan_domain_fuzz(domain):
    """
    Fuzz test for scan_domain() with a variety of domain inputs.
    This test ensures that scan_domain() does not raise exceptions and
    handles all inputs gracefully.
    """
    result = scan_domain(domain)

    # Must always return a dict
    assert isinstance(result, dict)

    # Must either succeed or fail gracefully
    assert "tls_version" in result or "error" in result

    # If error exists, it must be a string
    if "error" in result:
        assert isinstance(result["error"], str)

    # If tls_version exists, it must be a string or None
    if "tls_version" in result:
        assert result["tls_version"] is None or isinstance(result["tls_version"], str)

    # Allowed keys based on your TLSScanResults structure
    allowed_keys = {
        "domain",
        "port",
        "tls_version",
        "cipher_suite",
        "cipher_strength",
        "certificate_subject",
        "certificate_issuer",
        "not_before",
        "not_after",
        "key_size",
        "error",
        "scan_time_seconds",
    }

    # Single fast, correct check
    assert (
        set(result.keys()) <= allowed_keys
    ), f"Unexpected keys: {set(result.keys()) - allowed_keys}"
