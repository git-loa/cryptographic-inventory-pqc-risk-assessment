"""Tests for TLS scanning and evidence collection."""

import socket
import ssl
from unittest.mock import Mock, patch


from src.collection import tls_scanner
from src.collection.scan_results import create_scan_state


def make_state():
    """Create a scan state for unit tests."""
    return create_scan_state(
        target="example.com",
        target_type="domain",
        port=443,
    )


def test_collect_tls_details_success():
    """Collect the negotiated TLS version and cipher details."""
    state = make_state()
    tls_socket = Mock()

    tls_socket.cipher.return_value = (
        "TLS_AES_128_GCM_SHA256",
        "TLSv1.3",
        128,
    )
    tls_socket.version.return_value = "TLSv1.3"

    result = tls_scanner.collect_tls_details(state, tls_socket)

    assert result is True
    assert state.result["tls_version"] == "TLSv1.3"
    assert state.result["cipher_suite"] == "TLS_AES_128_GCM_SHA256"
    assert state.result["cipher_strength"] == 128
    assert state.result["diagnostics"] == []


def test_collect_tls_details_without_cipher():
    """Fail collection when no cipher suite was negotiated."""
    state = make_state()
    tls_socket = Mock()
    tls_socket.cipher.return_value = None

    result = tls_scanner.collect_tls_details(state, tls_socket)

    assert result is False
    assert state.result["scan_status"] == "failed"
    assert state.result["diagnostics"][0]["code"] == "NO_CIPHER_NEGOTIATED"


def test_collect_certificate_evidence_success():
    """Store parsed certificate metadata in the scan result."""
    state = make_state()
    tls_socket = Mock()
    tls_socket.getpeercert.return_value = b"certificate-der"

    certificate_info = {
        "public_key_algorithm": "RSA",
        "key_size": 2048,
        "certificate_serial_number": "12345",
    }

    with patch.object(
        tls_scanner,
        "parse_certificate",
        return_value=certificate_info,
    ) as parser:
        result = tls_scanner.collect_certificate_evidence(
            state,
            tls_socket,
        )

    assert result is True
    parser.assert_called_once_with(b"certificate-der")
    assert state.result["public_key_algorithm"] == "RSA"
    assert state.result["key_size"] == 2048
    assert state.result["certificate_serial_number"] == "12345"


def test_collect_certificate_evidence_without_certificate():
    """Report failure when the TLS peer provides no certificate."""
    state = make_state()
    tls_socket = Mock()
    tls_socket.getpeercert.return_value = None

    result = tls_scanner.collect_certificate_evidence(
        state,
        tls_socket,
    )

    assert result is False
    assert state.result["scan_status"] == "failed"
    assert state.result["diagnostics"][0]["code"] == "NO_PEER_CERTIFICATE"


def test_collect_certificate_evidence_parsing_failure():
    """Record a partial scan when certificate parsing fails."""
    state = make_state()
    tls_socket = Mock()
    tls_socket.getpeercert.return_value = b"invalid-certificate"

    with patch.object(
        tls_scanner,
        "parse_certificate",
        side_effect=ValueError("Invalid certificate"),
    ):
        result = tls_scanner.collect_certificate_evidence(
            state,
            tls_socket,
        )

    assert result is False
    assert state.result["scan_status"] == "partial"
    assert state.result["diagnostics"][0]["code"] == "CERTIFICATE_PARSING_FAILED"
    assert state.result["diagnostics"][0]["message"] == "Invalid certificate"


def test_collect_key_establishment_evidence_success():
    """Record an observed key-establishment group."""
    state = make_state()

    with patch.object(
        tls_scanner,
        "collect_key_establishment_group",
        return_value=("X25519", "observed"),
    ) as collector:
        tls_scanner.collect_key_establishment_evidence(
            state,
            target="example.com",
            port=443,
            timeout=5.0,
        )

    collector.assert_called_once_with(
        "example.com",
        port=443,
        timeout=5.0,
    )
    assert state.result["key_establishment_group"] == "X25519"
    assert state.result["key_establishment_evidence_status"] == "observed"
    assert (
        state.result["key_establishment_source"]
        == "openssl_s_client_separate_handshake"
    )


def test_collect_key_establishment_evidence_failure():
    """Record unavailable evidence when the probe raises an error."""
    state = make_state()

    with patch.object(
        tls_scanner,
        "collect_key_establishment_group",
        side_effect=OSError("OpenSSL unavailable"),
    ):
        tls_scanner.collect_key_establishment_evidence(
            state,
            target="example.com",
            port=443,
            timeout=5.0,
        )

    assert state.result["key_establishment_group"] is None
    assert state.result["key_establishment_evidence_status"] == "unavailable"
    assert state.result["key_establishment_source"] is None
    assert (
        state.result["diagnostics"][0]["code"] == "KEY_ESTABLISHMENT_PROBE_UNAVAILABLE"
    )


def test_scan_target_rejects_invalid_port():
    """Return a structured failure when the port is invalid."""
    result = tls_scanner.scan_target("example.com", port=70000)

    assert result["scan_status"] == "failed"
    assert result["diagnostics"][0]["code"] == "INVALID_SCAN_INPUT"
    assert result["diagnostics"][0]["category"] == "input_validation"
    assert result["completed_at"] is not None


def test_scan_target_rejects_invalid_timeout():
    """Return a structured failure when the timeout is invalid."""
    result = tls_scanner.scan_target("example.com", timeout=0)

    assert result["scan_status"] == "failed"
    assert result["diagnostics"][0]["code"] == "INVALID_SCAN_INPUT"
    assert result["diagnostics"][0]["category"] == "input_validation"
    assert result["completed_at"] is not None


def test_scan_target_rejects_invalid_hostname():
    """Return a structured failure when the hostname is invalid."""
    result = tls_scanner.scan_target("invalid_hostname")

    assert result["scan_status"] == "failed"
    assert result["diagnostics"][0]["code"] == "INVALID_SCAN_INPUT"
    assert result["diagnostics"][0]["category"] == "input_validation"
    assert result["completed_at"] is not None


# ---------------------------------------------------------
# Connection and TLS error handling
# ---------------------------------------------------------


def assert_structured_failure(result, expected_code):
    """Verify the common structure of a failed scan."""
    assert result["scan_status"] == "failed"
    assert result["completed_at"] is not None
    assert result["diagnostics"]

    diagnostic = result["diagnostics"][-1]

    assert diagnostic["code"] == expected_code
    assert diagnostic["severity"] == "error"


def mock_resolved_target():
    """Return a predictable resolved target for scanner tests."""
    return tls_scanner.ResolvedTarget(
        hostname="example.com",
        ip_address="203.0.113.10",
        port=443,
    )


@patch.object(
    tls_scanner,
    "resolve_target",
    side_effect=socket.gaierror("Name resolution failed"),
)
def test_scan_target_handles_dns_resolution_failure(mock_resolve):
    result = tls_scanner.scan_target("example.com")

    assert_structured_failure(result, "DNS_RESOLUTION_FAILED")

    diagnostic = result["diagnostics"][0]
    assert diagnostic["category"] == "connection"
    assert diagnostic["stage"] == "dns_resolution"

    mock_resolve.assert_called_once()


@patch.object(
    tls_scanner.socket,
    "create_connection",
    side_effect=ConnectionRefusedError("Connection refused"),
)
@patch.object(tls_scanner, "resolve_target")
def test_scan_target_handles_connection_refusal(
    mock_resolve,
    mock_connection,
):
    mock_resolve.return_value = mock_resolved_target()

    result = tls_scanner.scan_target("example.com")

    assert_structured_failure(result, "TLS_CONNECTION_FAILED")

    diagnostic = result["diagnostics"][0]
    assert diagnostic["category"] == "connection"
    assert diagnostic["stage"] == "tcp_connection"

    mock_resolve.assert_called_once()
    mock_connection.assert_called_once()


@patch.object(
    tls_scanner.socket,
    "create_connection",
    side_effect=socket.timeout("Connection timed out"),
)
@patch.object(tls_scanner, "resolve_target")
def test_scan_target_handles_connection_timeout(
    mock_resolve,
    mock_connection,
):
    mock_resolve.return_value = mock_resolved_target()

    result = tls_scanner.scan_target("example.com")

    assert_structured_failure(result, "TLS_CONNECTION_TIMEOUT")

    diagnostic = result["diagnostics"][0]
    assert diagnostic["category"] == "timeout"
    assert diagnostic["stage"] == "tls_connection"

    mock_resolve.assert_called_once()
    mock_connection.assert_called_once()


@patch.object(tls_scanner.ssl, "create_default_context")
@patch.object(tls_scanner.socket, "create_connection")
@patch.object(tls_scanner, "resolve_target")
def test_scan_target_handles_tls_handshake_failure(
    mock_resolve,
    mock_connection,
    mock_context,
):
    mock_resolve.return_value = mock_resolved_target()
    mock_connection.return_value.__enter__.return_value = Mock()

    mock_context.return_value.wrap_socket.side_effect = ssl.SSLError("Handshake failed")

    result = tls_scanner.scan_target("example.com")

    assert_structured_failure(result, "TLS_HANDSHAKE_FAILED")

    diagnostic = result["diagnostics"][0]
    assert diagnostic["category"] == "connection"
    assert diagnostic["stage"] == "tls_handshake"

    mock_resolve.assert_called_once()
    mock_connection.assert_called_once()


@patch.object(tls_scanner.ssl, "create_default_context")
@patch.object(tls_scanner.socket, "create_connection")
@patch.object(tls_scanner, "resolve_target")
def test_scan_target_handles_certificate_verification_failure(
    mock_resolve,
    mock_connection,
    mock_context,
):
    mock_resolve.return_value = mock_resolved_target()
    mock_connection.return_value.__enter__.return_value = Mock()

    mock_context.return_value.wrap_socket.side_effect = ssl.SSLCertVerificationError(
        1,
        "Certificate verification failed",
    )

    result = tls_scanner.scan_target("example.com")

    assert_structured_failure(
        result,
        "CERTIFICATE_VERIFICATION_FAILED",
    )

    assert result["certificate_verification_status"] == "failed"
    assert result["certificate_verification_error"] == "Certificate verification failed"

    diagnostic = result["diagnostics"][0]
    assert diagnostic["category"] == "certificate"
    assert diagnostic["stage"] == "certificate_verification"

    mock_resolve.assert_called_once()
    mock_connection.assert_called_once()


# ---------------------------------------------------------
# Successful scanner orchestration
# ---------------------------------------------------------


@patch.object(
    tls_scanner,
    "collect_key_establishment_evidence",
)
@patch.object(
    tls_scanner,
    "collect_certificate_evidence",
    return_value=True,
)
@patch.object(
    tls_scanner,
    "collect_tls_details",
    return_value=True,
)
@patch.object(tls_scanner, "resolve_target")
@patch.object(tls_scanner.ssl, "create_default_context")
@patch.object(tls_scanner.socket, "create_connection")
def test_scan_target_successfully_coordinates_collection(
    mock_connection,
    mock_context,
    mock_resolve,
    mock_tls_details,
    mock_certificate,
    mock_key_establishment,
):
    mock_resolve.return_value = tls_scanner.ResolvedTarget(
        hostname="example.com",
        ip_address="203.0.113.10",
        port=443,
    )

    mock_connection.return_value.__enter__.return_value = Mock()

    mock_tls_socket = Mock()
    mock_context.return_value.wrap_socket.return_value.__enter__.return_value = (
        mock_tls_socket
    )

    result = tls_scanner.scan_target(
        "example.com",
        port=443,
        timeout=5.0,
    )

    assert result["scan_status"] == "completed"
    assert result["completed_at"] is not None
    assert result["resolved_ip_address"] == "203.0.113.10"
    assert result["certificate_verification_status"] == "verified"
    assert result["certificate_verification_error"] is None
    assert result["diagnostics"] == []

    mock_resolve.assert_called_once_with(
        "example.com",
        "domain",
        443,
    )

    mock_connection.assert_called_once_with(
        ("203.0.113.10", 443),
        timeout=5.0,
    )

    mock_tls_details.assert_called_once()
    mock_certificate.assert_called_once()

    mock_key_establishment.assert_called_once_with(
        mock_key_establishment.call_args.args[0],
        target="example.com",
        port=443,
        timeout=5.0,
    )
