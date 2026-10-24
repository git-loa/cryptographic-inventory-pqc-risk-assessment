"""Canonical TLS scan-result construction and error finalization."""

from __future__ import annotations

import socket
import ssl
import time
import uuid
from dataclasses import dataclass

from src.collection.models import (
    SCAN_SCHEMA_VERSION,
    DiagnosticCategory,
    ScanDiagnostic,
    TLSScanResult,
    TargetType,
)
from src.collection.tls_utils import make_diagnostic, utc_now


@dataclass(slots=True)
class ScanState:
    """Hold the result and timing information for one scan."""

    started_at: str
    start_time: float
    result: TLSScanResult


def new_scan_result(
    target: str,
    target_type: TargetType,
    port: int,
    scan_id: str,
    started_at: str,
) -> TLSScanResult:
    """Create a result with all mandatory contract fields populated."""

    return {
        "schema_version": SCAN_SCHEMA_VERSION,
        "scan_id": scan_id,
        "target": target,
        "target_type": target_type,
        "port": port,
        "resolved_ip_address": None,
        "scan_status": "failed",
        "started_at": started_at,
        "completed_at": None,
        "scan_time_seconds": 0.0,
        "certificate_verification_status": "unknown",
        "certificate_verification_error": None,
        "key_establishment_evidence_status": "not_attempted",
        "diagnostics": [],
    }


def create_scan_state(
    target: str,
    target_type: TargetType,
    port: int,
) -> ScanState:
    """Initialize the result and timing state for a scan."""

    started_at = utc_now()
    start_time = time.perf_counter()

    result = new_scan_result(
        target=target,
        target_type=target_type,
        port=port,
        scan_id=str(uuid.uuid4()),
        started_at=started_at,
    )

    return ScanState(
        started_at=started_at,
        start_time=start_time,
        result=result,
    )


def add_diagnostic(
    state: ScanState,
    diagnostic: ScanDiagnostic,
) -> None:
    """Append a diagnostic to the scan result."""

    state.result["diagnostics"].append(diagnostic)


def finish_scan(state: ScanState) -> TLSScanResult:
    """Finalize timing metadata and return the scan result."""

    result = state.result

    result["scan_time_seconds"] = max(
        0.0,
        time.perf_counter() - state.start_time,
    )
    result["completed_at"] = utc_now()

    return result


def fail_scan(
    state: ScanState,
    message: str,
    category: DiagnosticCategory,
    stage: str,
    code: str,
) -> TLSScanResult:
    """Record a fatal diagnostic and finalize the failed scan."""

    add_diagnostic(
        state,
        make_diagnostic(
            code=code,
            category=category,
            severity="error",
            message=message,
            stage=stage,
        ),
    )

    state.result["scan_status"] = "failed"

    return finish_scan(state)


def handle_connection_error(
    state: ScanState,
    error: Exception,
) -> TLSScanResult:
    """Translate a connection error into a structured scan failure."""

    if isinstance(error, ssl.SSLCertVerificationError):
        state.result["certificate_verification_status"] = "failed"
        state.result["certificate_verification_error"] = str(error)

        return fail_scan(
            state=state,
            message=str(error),
            category="certificate",
            stage="certificate_verification",
            code="CERTIFICATE_VERIFICATION_FAILED",
        )

    if isinstance(error, socket.timeout):
        return fail_scan(
            state=state,
            message=str(error) or "TLS connection timed out.",
            category="timeout",
            stage="tls_connection",
            code="TLS_CONNECTION_TIMEOUT",
        )

    if isinstance(error, socket.gaierror):
        return fail_scan(
            state=state,
            message=str(error),
            category="connection",
            stage="dns_resolution",
            code="DNS_RESOLUTION_FAILED",
        )

    if isinstance(error, ssl.SSLError):
        return fail_scan(
            state=state,
            message=str(error),
            category="connection",
            stage="tls_handshake",
            code="TLS_HANDSHAKE_FAILED",
        )

    if isinstance(error, OSError):
        return fail_scan(
            state=state,
            message=str(error),
            category="connection",
            stage="tcp_connection",
            code="TLS_CONNECTION_FAILED",
        )

    return fail_scan(
        state=state,
        message=str(error) or "Unexpected collection error.",
        category="internal",
        stage="collection",
        code="COLLECTION_INTERNAL_ERROR",
    )
