"""Property-based tests for TLS scanner input handling.

Hypothesis generates malformed, unusual, and valid-looking inputs.
The TLS connection routine is mocked so fuzzing never accesses the network.
"""

import math
from unittest.mock import patch

from hypothesis import given, settings, strategies as st

from src.collection.tls_scanner import scan_domain, validate_domain_or_error

# ---------------------------------------------------------------------------

# Input strategies

# ---------------------------------------------------------------------------

random_text = st.text(max_size=300)

random_bytes_as_text = st.binary(max_size=300).map(
    lambda value: value.decode("utf-8", errors="replace")
)

domain_like = st.from_regex(
    r"[a-zA-Z0-9-]{1,20}(\.[a-zA-Z0-9-]{1,20})+",
    fullmatch=True,
)

malformed_domains = st.sampled_from(
    [
        "",
        ".example.com",
        "example..com",
        "example",
        "exa mple.com",
        "example!.com",
        "-example.com",
        "example-.com",
        "example.com.",
        "localhost",
        "a" * 254 + ".com",
        "mañana.com",
        "xn--d1acufc.xn--p1ai",
        "😀.com",
    ]
)

domain_strategy = st.one_of(
    random_text,
    random_bytes_as_text,
    domain_like,
    malformed_domains,
    st.none(),
    st.integers(),
    st.lists(st.text(max_size=20), max_size=5),
    st.dictionaries(
        st.text(max_size=10),
        st.text(max_size=10),
        max_size=5,
    ),
)

port_strategy = st.one_of(
    st.integers(min_value=-1000, max_value=100000),
    st.none(),
    st.text(max_size=10),
    st.booleans(),
    st.floats(
        allow_nan=False,
        allow_infinity=False,
        width=32,
    ),
)

timeout_strategy = st.one_of(
    st.integers(min_value=-100, max_value=100),
    st.floats(
        allow_nan=True,
        allow_infinity=True,
        width=32,
    ),
    st.none(),
    st.text(max_size=10),
    st.booleans(),
)

# ---------------------------------------------------------------------------

# Deterministic mock result

# ---------------------------------------------------------------------------


def fake_connection_result(domain, port, timeout, start):
    """Return a stable result representing successful TLS collection."""

    return {
        "domain": domain,
        "port": port,
        "scan_status": "success",
        "tls_version": "TLSv1.3",
        "cipher_suite": "TLS_AES_256_GCM_SHA384",
        "cipher_strength": 256,
        "certificate_subject": {},
        "certificate_issuer": {},
        "not_before": None,
        "not_after": None,
        "key_size": 2048,
        "public_key_algorithm": "RSA",
        "public_key_variant": None,
        "public_key_algorithm_oid": "1.2.840.113549.1.1.1",
        "certificate_version": "v3",
        "certificate_serial_number": "12345",
        "certificate_signature_algorithm_oid": "1.2.840.113549.1.1.11",
        "certificate_signature_hash_algorithm": "sha256",
        "public_key_curve": None,
        "rsa_public_exponent": 65537,
        "san_dns_names": [],
        "san_ip_addresses": [],
        "key_usage": None,
        "extended_key_usage": None,
        "basic_constraints": None,
        "key_establishment_group": "X25519",
        "key_establishment_evidence_status": "observed",
        "key_establishment_source": "openssl_s_client_separate_handshake",
        "scan_time_seconds": 0.01,
    }


def assert_result_contract(result):
    """Check the structural invariants shared by scan results."""

    assert isinstance(result, dict)
    assert result["scan_status"] in {"success", "failed"}

    assert isinstance(result["domain"], str)

    port = result["port"]

    assert port is None or (
        isinstance(port, int) and not isinstance(port, bool) and 1 <= port <= 65535
    )

    assert isinstance(result["scan_time_seconds"], (int, float))
    assert math.isfinite(result["scan_time_seconds"])
    assert result["scan_time_seconds"] >= 0

    assert result["key_establishment_evidence_status"] in {
        "observed",
        "unavailable",
        "not_attempted",
    }

    if result["scan_status"] == "failed":
        assert isinstance(result.get("error"), str)
        assert result["error"].strip()

    else:
        # A successful scan must identify a valid endpoint.
        assert isinstance(result["port"], int)
        assert not isinstance(result["port"], bool)
        assert 1 <= result["port"] <= 65535


def is_valid_port(port):
    """Return whether a generated value satisfies the port contract."""

    return isinstance(port, int) and not isinstance(port, bool) and 1 <= port <= 65535


def is_valid_timeout(timeout):
    """Return whether a generated value satisfies the timeout contract."""

    return (
        isinstance(timeout, (int, float))
        and not isinstance(timeout, bool)
        and math.isfinite(timeout)
        and timeout > 0
    )


# ---------------------------------------------------------------------------

# Domain input fuzzing

# ---------------------------------------------------------------------------


@settings(max_examples=300, deadline=None)
@given(domain=domain_strategy)
def test_scan_domain_handles_generated_inputs_without_network(domain):
    """Generated domain inputs must not crash or access the network."""

    with patch(
        "src.collection.tls_scanner._scan_tls_connection",
        side_effect=fake_connection_result,
    ) as connection:
        result = scan_domain(domain)

    assert_result_contract(result)

    validation_error = validate_domain_or_error(domain, 443)

    if validation_error is not None:
        assert result["scan_status"] == "failed"
        assert result["error"] == "Invalid domain name"
        connection.assert_not_called()
    else:
        connection.assert_called_once()

        assert result["domain"] == domain
        assert result["port"] == 443


# ---------------------------------------------------------------------------

# Port input fuzzing

# ---------------------------------------------------------------------------


@settings(max_examples=200, deadline=None)
@given(port=port_strategy)
def test_scan_domain_handles_generated_ports_without_network(port):
    """Port validation must prevent invalid values reaching collection."""

    with patch(
        "src.collection.tls_scanner._scan_tls_connection",
        side_effect=fake_connection_result,
    ) as connection:
        result = scan_domain("example.com", port=port)

    assert_result_contract(result)

    if is_valid_port(port):
        connection.assert_called_once()
        assert result["port"] == port
    else:
        assert result["scan_status"] == "failed"
        assert result["error"] == "Invalid port"
        assert result["port"] is None
        connection.assert_not_called()


# ---------------------------------------------------------------------------

# Timeout input fuzzing

# ---------------------------------------------------------------------------


@settings(max_examples=200, deadline=None)
@given(timeout=timeout_strategy)
def test_scan_domain_handles_generated_timeouts_without_network(timeout):
    """Timeout validation must prevent invalid values reaching collection."""

    with patch(
        "src.collection.tls_scanner._scan_tls_connection",
        side_effect=fake_connection_result,
    ) as connection:
        result = scan_domain("example.com", timeout=timeout)

    assert_result_contract(result)

    if is_valid_timeout(timeout) and timeout <= 300:
        assert result["scan_status"] == "success"
        connection.assert_called_once()
        assert result["port"] == 443

        args = connection.call_args.args
        assert args[2] == float(timeout)

    else:
        assert result["scan_status"] == "failed"
        assert result["error"] == "Invalid timeout"
        connection.assert_not_called()
