"""Tests for canonical TLS scan results and error handling."""

import socket
import ssl

import pytest

from src.collection.scan_results import (
    create_scan_state,
    fail_scan,
    finish_scan,
    handle_connection_error,
)


def make_state():
    return create_scan_state(
        target="example.com",
        target_type="domain",
        port=443,
    )


@pytest.mark.parametrize(
    ("error", "expected_code"),
    [
        (
            socket.timeout("connection timed out"),
            "TLS_CONNECTION_TIMEOUT",
        ),
        (
            socket.gaierror("name resolution failed"),
            "DNS_RESOLUTION_FAILED",
        ),
        (
            ssl.SSLError("TLS handshake failed"),
            "TLS_HANDSHAKE_FAILED",
        ),
        (
            OSError("connection refused"),
            "TLS_CONNECTION_FAILED",
        ),
        (
            RuntimeError("unexpected failure"),
            "COLLECTION_INTERNAL_ERROR",
        ),
    ],
)
def test_handle_connection_error(error, expected_code):
    state = make_state()

    result = handle_connection_error(state, error)

    assert result["scan_status"] == "failed"
    assert result["completed_at"] is not None
    assert result["diagnostics"]

    diagnostic = result["diagnostics"][-1]

    assert diagnostic["code"] == expected_code
    assert diagnostic["severity"] == "error"
    assert diagnostic["message"] == str(error)


def test_certificate_verification_error_updates_verification_status():
    state = make_state()

    error = ssl.SSLCertVerificationError("certificate has expired")

    result = handle_connection_error(state, error)

    assert result["scan_status"] == "failed"
    assert result["certificate_verification_status"] == "failed"
    assert result["certificate_verification_error"] == str(error)

    diagnostic = result["diagnostics"][-1]

    assert diagnostic["code"] == "CERTIFICATE_VERIFICATION_FAILED"
    assert diagnostic["category"] == "certificate"
    assert diagnostic["stage"] == "certificate_verification"


def test_fail_scan_records_diagnostic_and_finalizes_result():
    state = make_state()

    result = fail_scan(
        state=state,
        message="Invalid scan input",
        category="input_validation",
        stage="input_validation",
        code="INVALID_SCAN_INPUT",
    )

    assert result["scan_status"] == "failed"
    assert result["completed_at"] is not None

    diagnostic = result["diagnostics"][-1]

    assert diagnostic["code"] == "INVALID_SCAN_INPUT"
    assert diagnostic["message"] == "Invalid scan input"
    assert diagnostic["category"] == "input_validation"


def test_finish_scan_populates_timing_metadata():
    state = make_state()

    result = finish_scan(state)

    assert result["completed_at"] is not None
    assert isinstance(result["scan_time_seconds"], float)
    assert result["scan_time_seconds"] >= 0
