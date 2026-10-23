"""Unit tests for TLS endpoint collection.

All network operations are mocked. These tests must not require internet
access or depend on the TLS configuration of a public endpoint.
"""

import socket
import ssl
from unittest.mock import MagicMock, patch

import pytest

from src.collection.tls_scanner import scan_domain, validate_domain_or_error

DOMAIN = "example.com"

CERTIFICATE_INFO = {
    "certificate_version": "v3",
    "certificate_serial_number": "12345",
    "certificate_subject": {"2.5.4.3": DOMAIN},
    "certificate_issuer": {"2.5.4.3": "Example CA"},
    "not_before": "2026-01-01T00:00:00+00:00",
    "not_after": "2027-01-01T00:00:00+00:00",
    "public_key_algorithm": "RSA",
    "public_key_variant": None,
    "public_key_algorithm_oid": "1.2.840.113549.1.1.1",
    "key_size": 2048,
    "public_key_curve": None,
    "rsa_public_exponent": 65537,
    "certificate_signature_algorithm_oid": "1.2.840.113549.1.1.11",
    "certificate_signature_hash_algorithm": "sha256",
    "san_dns_names": [DOMAIN],
    "san_ip_addresses": [],
    "key_usage": None,
    "extended_key_usage": None,
    "basic_constraints": None,
}


def make_successful_tls():
    """Create a mock TLS connection and its supporting context."""

    tls = MagicMock()
    tls.cipher.return_value = (
        "TLS_AES_256_GCM_SHA384",
        "TLSv1.3",
        256,
    )
    tls.version.return_value = "TLSv1.3"
    tls.getpeercert.return_value = b"fake-der-certificate"

    context = MagicMock()
    context.wrap_socket.return_value.__enter__.return_value = tls

    raw_socket = MagicMock()
    connection = MagicMock()
    connection.__enter__.return_value = raw_socket

    return tls, context, connection


def assert_common_result_fields(result):
    """Verify the minimum result contract shared by scan outcomes."""

    assert isinstance(result, dict)
    assert isinstance(result["domain"], str)

    port = result["port"]

    assert port is None or (
        isinstance(port, int) and not isinstance(port, bool) and 1 <= port <= 65535
    )

    assert result["scan_status"] in {"success", "failed"}

    assert isinstance(result["scan_time_seconds"], (int, float))
    assert result["scan_time_seconds"] >= 0

    assert result["key_establishment_evidence_status"] in {
        "observed",
        "unavailable",
        "not_attempted",
    }


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "domain",
    [
        "",
        ".example.com",
        "example..com",
        "example",
        "exa mple.com",
        "-example.com",
        "example-.com",
        "example!.com",
        "a" * 254 + ".com",
    ],
)
def test_invalid_domain_is_rejected_without_network_access(domain):
    with patch("src.collection.tls_scanner.socket.create_connection") as connect:
        result = scan_domain(domain)

    assert result["scan_status"] == "failed"
    assert result["error"] == "Invalid domain name"
    assert result["key_establishment_evidence_status"] == "not_attempted"
    connect.assert_not_called()


@pytest.mark.parametrize("domain", [None, 123, [], {}, True])
def test_non_string_domain_is_rejected(domain):
    with patch("src.collection.tls_scanner.socket.create_connection") as connect:
        result = scan_domain(domain)

    assert result["scan_status"] == "failed"
    assert result["error"] == "Invalid domain name"
    connect.assert_not_called()


@pytest.mark.parametrize("port", [0, -1, 65536, 443.5, "443", None, True])
def test_invalid_port_is_rejected_without_network_access(port):
    with patch("src.collection.tls_scanner.socket.create_connection") as connect:
        result = scan_domain(DOMAIN, port=port)

    assert result["scan_status"] == "failed"
    assert result["error"] == "Invalid port"
    assert result["port"] is None
    assert result["key_establishment_evidence_status"] == "not_attempted"
    connect.assert_not_called()


@pytest.mark.parametrize(
    "timeout",
    [
        0,
        -1,
        float("nan"),
        float("inf"),
        float("-inf"),
        "5",
        None,
        True,
        10**1000,
        301,
    ],
)
def test_invalid_timeout_is_rejected_without_network_access(timeout):
    with patch("src.collection.tls_scanner.socket.create_connection") as connect:
        result = scan_domain(DOMAIN, timeout=timeout)

    assert result["scan_status"] == "failed"
    assert result["error"] == "Invalid timeout"
    assert result["key_establishment_evidence_status"] == "not_attempted"
    connect.assert_not_called()


def test_maximum_timeout_is_accepted():
    with patch(
        "src.collection.tls_scanner._scan_tls_connection",
        return_value={"scan_status": "success"},
    ) as scan:
        result = scan_domain(
            DOMAIN,
            timeout=300,
        )

    assert result["scan_status"] == "success"

    scan.assert_called_once()
    args = scan.call_args.args

    assert args[0] == DOMAIN
    assert args[1] == 443
    assert args[2] == 300.0


def test_validate_domain_accepts_normal_hostname():
    assert validate_domain_or_error(DOMAIN, 443) is None


def test_validate_domain_accepts_valid_port_boundaries():
    assert validate_domain_or_error(DOMAIN, 1) is None
    assert validate_domain_or_error(DOMAIN, 65535) is None


# ---------------------------------------------------------------------------
# Successful collection
# ---------------------------------------------------------------------------


def test_successful_tls_scan_collects_connection_and_certificate_evidence():
    tls, context, connection = make_successful_tls()

    with (
        patch(
            "src.collection.tls_scanner.ssl.create_default_context",
            return_value=context,
        ),
        patch(
            "src.collection.tls_scanner.socket.create_connection",
            return_value=connection,
        ) as connect,
        patch(
            "src.collection.tls_scanner.parse_certificate",
            return_value=CERTIFICATE_INFO,
        ) as parse_cert,
        patch(
            "src.collection.tls_scanner.collect_key_establishment_group",
            return_value=("X25519", "observed"),
        ) as key_probe,
    ):
        result = scan_domain(DOMAIN, port=443, timeout=3)

    assert_common_result_fields(result)

    assert result["scan_status"] == "success"
    assert result["tls_version"] == "TLSv1.3"
    assert result["cipher_suite"] == "TLS_AES_256_GCM_SHA384"
    assert result["cipher_strength"] == 256

    assert result["public_key_algorithm"] == "RSA"
    assert result["key_size"] == 2048
    assert result["certificate_subject"] == CERTIFICATE_INFO["certificate_subject"]

    assert result["key_establishment_group"] == "X25519"
    assert result["key_establishment_evidence_status"] == "observed"
    assert result["key_establishment_source"] == "openssl_s_client_separate_handshake"

    connect.assert_called_once_with((DOMAIN, 443), timeout=3.0)
    parse_cert.assert_called_once_with(b"fake-der-certificate")
    key_probe.assert_called_once_with(DOMAIN, port=443, timeout=3.0)

    tls.cipher.assert_called_once()


def test_successful_tls_scan_without_key_establishment_evidence():
    _, context, connection = make_successful_tls()

    with (
        patch(
            "src.collection.tls_scanner.ssl.create_default_context",
            return_value=context,
        ),
        patch(
            "src.collection.tls_scanner.socket.create_connection",
            return_value=connection,
        ),
        patch(
            "src.collection.tls_scanner.parse_certificate",
            return_value=CERTIFICATE_INFO,
        ),
        patch(
            "src.collection.tls_scanner.collect_key_establishment_group",
            return_value=(None, "unavailable"),
        ),
    ):
        result = scan_domain(DOMAIN)

    assert result["scan_status"] == "success"
    assert result["key_establishment_group"] is None
    assert result["key_establishment_evidence_status"] == "unavailable"
    assert result["key_establishment_source"] is None


# ---------------------------------------------------------------------------
# Connection and TLS failures
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("error", "message_fragment"),
    [
        (socket.gaierror("name resolution failed"), "DNS error"),
        (socket.timeout("connection timed out"), "Timeout"),
        (ConnectionRefusedError("connection refused"), "Connection error"),
        (ssl.SSLError("handshake failed"), "SSL error"),
    ],
)
def test_connection_failures_return_structured_results(error, message_fragment):
    with patch(
        "src.collection.tls_scanner.socket.create_connection",
        side_effect=error,
    ):
        result = scan_domain(DOMAIN)

    assert_common_result_fields(result)

    assert result["scan_status"] == "failed"
    assert message_fragment in result["error"]
    assert result["key_establishment_evidence_status"] == "not_attempted"
    assert result["key_establishment_group"] is None
    assert result["key_establishment_source"] is None


def test_no_negotiated_cipher_returns_failure():
    _, context, connection = make_successful_tls()
    context.wrap_socket.return_value.__enter__.return_value.cipher.return_value = None

    with (
        patch(
            "src.collection.tls_scanner.ssl.create_default_context",
            return_value=context,
        ),
        patch(
            "src.collection.tls_scanner.socket.create_connection",
            return_value=connection,
        ),
        patch(
            "src.collection.tls_scanner.collect_key_establishment_group"
        ) as key_probe,
    ):
        result = scan_domain(DOMAIN)

    assert result["scan_status"] == "failed"
    assert result["error"] == "No cipher suite negotiated"
    assert result["key_establishment_evidence_status"] == "not_attempted"
    key_probe.assert_not_called()


def test_missing_peer_certificate_returns_failure():
    _, context, connection = make_successful_tls()
    context.wrap_socket.return_value.__enter__.return_value.getpeercert.return_value = (
        None
    )

    with (
        patch(
            "src.collection.tls_scanner.ssl.create_default_context",
            return_value=context,
        ),
        patch(
            "src.collection.tls_scanner.socket.create_connection",
            return_value=connection,
        ),
        patch("src.collection.tls_scanner.parse_certificate") as parse_cert,
        patch(
            "src.collection.tls_scanner.collect_key_establishment_group"
        ) as key_probe,
    ):
        result = scan_domain(DOMAIN)

    assert result["scan_status"] == "failed"
    assert result["error"] == "No certificate returned by server"
    assert result["key_establishment_evidence_status"] == "not_attempted"

    parse_cert.assert_not_called()
    key_probe.assert_not_called()


def test_certificate_parsing_value_error_returns_failure():
    _, context, connection = make_successful_tls()

    with (
        patch(
            "src.collection.tls_scanner.ssl.create_default_context",
            return_value=context,
        ),
        patch(
            "src.collection.tls_scanner.socket.create_connection",
            return_value=connection,
        ),
        patch(
            "src.collection.tls_scanner.parse_certificate",
            side_effect=ValueError("malformed DER"),
        ),
        patch(
            "src.collection.tls_scanner.collect_key_establishment_group"
        ) as key_probe,
    ):
        result = scan_domain(DOMAIN)

    assert result["scan_status"] == "failed"
    assert "Certificate parsing error" in result["error"]
    assert result["key_establishment_evidence_status"] == "not_attempted"
    key_probe.assert_not_called()


# ---------------------------------------------------------------------------
# Key-establishment probe failures
# ---------------------------------------------------------------------------


def test_key_probe_timeout_does_not_fail_successful_tls_scan():
    _, context, connection = make_successful_tls()

    with (
        patch(
            "src.collection.tls_scanner.ssl.create_default_context",
            return_value=context,
        ),
        patch(
            "src.collection.tls_scanner.socket.create_connection",
            return_value=connection,
        ),
        patch(
            "src.collection.tls_scanner.parse_certificate",
            return_value=CERTIFICATE_INFO,
        ),
        patch(
            "src.collection.tls_scanner.collect_key_establishment_group",
            side_effect=TimeoutError("probe timed out"),
        ),
    ):
        result = scan_domain(DOMAIN)

    assert result["scan_status"] == "success"
    assert result["key_establishment_group"] is None
    assert result["key_establishment_evidence_status"] == "unavailable"
    assert result["key_establishment_source"] is None


def test_result_contains_no_unexpected_fields():
    _, context, connection = make_successful_tls()

    with (
        patch(
            "src.collection.tls_scanner.ssl.create_default_context",
            return_value=context,
        ),
        patch(
            "src.collection.tls_scanner.socket.create_connection",
            return_value=connection,
        ),
        patch(
            "src.collection.tls_scanner.parse_certificate",
            return_value=CERTIFICATE_INFO,
        ),
        patch(
            "src.collection.tls_scanner.collect_key_establishment_group",
            return_value=("X25519", "observed"),
        ),
    ):
        result = scan_domain(DOMAIN)

    allowed_keys = {
        "domain",
        "port",
        "scan_status",
        "tls_version",
        "cipher_suite",
        "cipher_strength",
        "certificate_subject",
        "certificate_issuer",
        "not_before",
        "not_after",
        "key_size",
        "public_key_algorithm",
        "public_key_variant",
        "public_key_algorithm_oid",
        "error",
        "scan_time_seconds",
        "key_establishment_group",
        "key_establishment_evidence_status",
        "key_establishment_source",
        "rsa_public_exponent",
        "certificate_version",
        "certificate_serial_number",
        "certificate_signature_algorithm_oid",
        "certificate_signature_hash_algorithm",
        "key_usage",
        "extended_key_usage",
        "basic_constraints",
        "public_key_curve",
        "san_dns_names",
        "san_ip_addresses",
    }

    assert set(result).issubset(allowed_keys)
