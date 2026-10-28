"""Tests for TLS collection validation and utility functions."""

import socket

import pytest

from pqc_inventory.collection import tls_utils

# ---------------------------------------------------------------------------
# validate_target
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("target", "expected_type", "expected_target"),
    [
        ("example.com", "domain", "example.com"),
        ("EXAMPLE.COM", "domain", "example.com"),
        (" example.com ", "domain", "example.com"),
        ("example.com.", "domain", "example.com"),
        ("192.0.2.10", "ipv4", "192.0.2.10"),
        ("2001:db8::10", "ipv6", "2001:db8::10"),
    ],
)
def test_validate_target_accepts_valid_targets(
    target,
    expected_type,
    expected_target,
):
    """Accept valid domains and IP addresses in normalized form."""
    target_type, normalized_target = tls_utils.validate_target(target)

    assert target_type == expected_type
    assert normalized_target == expected_target


@pytest.mark.parametrize(
    "target",
    [
        "",
        " ",
        ".",
        "example",
        "-example.com",
        "example-.com",
        "example..com",
        "exa_mple.com",
        "example.com/path",
        "not-an-ipv6-address::xyz",
    ],
)
def test_validate_target_rejects_invalid_targets(target):
    """Reject empty, malformed, or unsupported targets."""
    with pytest.raises(ValueError):
        tls_utils.validate_target(target)


@pytest.mark.parametrize(
    "target",
    [
        None,
        123,
        [],
    ],
)
def test_validate_target_rejects_non_string_input(target):
    """Reject inputs that are not strings."""
    with pytest.raises((TypeError, ValueError)):
        tls_utils.validate_target(target)


def test_validate_target_normalizes_internationalized_domain():
    """Convert a valid internationalized domain to its ASCII representation."""
    target_type, normalized_target = tls_utils.validate_target("bücher.de")

    assert target_type == "domain"
    assert normalized_target == "xn--bcher-kva.de"


# ---------------------------------------------------------------------------
# validate_port
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("port", [1, 80, 443, 8443, 65535])
def test_validate_port_accepts_valid_ports(port):
    """Accept integer ports within the valid TCP/UDP port range."""
    assert tls_utils.validate_port(port) == port


@pytest.mark.parametrize(
    "port",
    [
        0,
        -1,
        65536,
        1.5,
        "443",
        None,
        True,
        False,
    ],
)
def test_validate_port_rejects_invalid_ports(port):
    """Reject ports outside the valid range or with an invalid type."""
    with pytest.raises((TypeError, ValueError)):
        tls_utils.validate_port(port)


# ---------------------------------------------------------------------------
# validate_timeout
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "timeout",
    [
        0.001,
        1,
        5.0,
        30,
        300,
    ],
)
def test_validate_timeout_accepts_valid_timeouts(timeout):
    """Accept finite, positive timeouts up to the configured maximum."""
    assert tls_utils.validate_timeout(timeout) == timeout


@pytest.mark.parametrize(
    "timeout",
    [
        0,
        -1,
        300.001,
        float("inf"),
        float("-inf"),
        float("nan"),
        True,
        False,
        "5",
        None,
    ],
)
def test_validate_timeout_rejects_invalid_timeouts(timeout):
    """Reject non-positive, non-finite, excessive, or non-numeric timeouts."""
    with pytest.raises((TypeError, ValueError)):
        tls_utils.validate_timeout(timeout)


# ---------------------------------------------------------------------------
# make_diagnostic
# ---------------------------------------------------------------------------


def test_make_diagnostic_returns_expected_fields():
    """Create a diagnostic with all required fields preserved."""
    diagnostic = tls_utils.make_diagnostic(
        code="TLS_CONNECTION_FAILED",
        category="connection",
        severity="error",
        message="The TLS connection could not be established.",
        stage="connect",
    )

    assert diagnostic == {
        "code": "TLS_CONNECTION_FAILED",
        "category": "connection",
        "severity": "error",
        "message": "The TLS connection could not be established.",
        "stage": "connect",
    }


# ---------------------------------------------------------------------------
# resolve_target
# ---------------------------------------------------------------------------


def test_resolve_target_resolves_domain(monkeypatch):
    """Resolve a domain and retain the requested hostname and port."""

    def fake_getaddrinfo(host, port, **kwargs):  # pylint: disable=unused-argument
        assert host == "example.com"
        assert port == 443

        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("192.0.2.10", port),
            )
        ]

    monkeypatch.setattr(
        tls_utils.socket,
        "getaddrinfo",
        fake_getaddrinfo,
    )

    resolved = tls_utils.resolve_target(
        target="example.com",
        target_type="domain",
        port=443,
    )

    assert resolved.hostname == "example.com"
    assert resolved.ip_address == "192.0.2.10"
    assert resolved.port == 443


def test_resolve_target_accepts_ipv4_address(monkeypatch):
    """Resolve an IPv4 target without changing its address."""

    def fake_getaddrinfo(host, port, **kwargs):  # pylint: disable=unused-argument
        assert host == "192.0.2.10"

        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("192.0.2.10", port),
            )
        ]

    monkeypatch.setattr(
        tls_utils.socket,
        "getaddrinfo",
        fake_getaddrinfo,
    )

    resolved = tls_utils.resolve_target(
        target="192.0.2.10",
        target_type="ipv4",
        port=443,
    )

    assert resolved.ip_address == "192.0.2.10"
    assert resolved.port == 443


def test_resolve_target_rejects_mismatched_target_type():
    """Reject an IP address when the supplied target type is incorrect."""
    with pytest.raises((TypeError, ValueError)):
        tls_utils.resolve_target(
            target="192.0.2.10",
            target_type="ipv6",
            port=443,
        )


def test_resolve_target_rejects_invalid_port():
    """Reject an invalid port before attempting DNS resolution."""
    with pytest.raises((TypeError, ValueError)):
        tls_utils.resolve_target(
            target="example.com",
            target_type="domain",
            port=65536,
        )


def test_resolve_target_handles_dns_failure(monkeypatch):
    """Propagate a DNS resolution failure from the resolver."""

    def fake_getaddrinfo(*args, **kwargs):
        raise socket.gaierror("Name resolution failed")

    monkeypatch.setattr(
        tls_utils.socket,
        "getaddrinfo",
        fake_getaddrinfo,
    )

    with pytest.raises(socket.gaierror):
        tls_utils.resolve_target(
            target="example.com",
            target_type="domain",
            port=443,
        )
