"""
Collect TLS connection and certificate evidence from an endpoint.

This module coordinates collection only. It does not determine whether an
endpoint is secure or post-quantum cryptography (PQC) ready.
"""

from __future__ import annotations

import socket
import ssl

from cryptography.exceptions import UnsupportedAlgorithm

from pqc_inventory.collection.certificate_parser import parse_certificate
from pqc_inventory.collection.key_establishment import collect_key_establishment_group
from pqc_inventory.collection.models import (
    TargetType,
    TLSScanResult,
)
from pqc_inventory.collection.scan_results import (
    ScanState,
    add_diagnostic,
    create_scan_state,
    fail_scan,
    finish_scan,
    handle_connection_error,
)
from pqc_inventory.collection.tls_utils import (
    ResolvedTarget,
    make_diagnostic,
    resolve_target,
    validate_port,
    validate_target,
    validate_timeout,
)
from pqc_inventory.utils.logger import get_logger

logger = get_logger(__name__)


def collect_tls_details(state: ScanState, tls_socket: ssl.SSLSocket) -> bool:
    """Collect the negotiated TLS version and cipher suite."""

    cipher = tls_socket.cipher()

    if cipher is None:
        add_diagnostic(
            state,
            make_diagnostic(
                code="NO_CIPHER_NEGOTIATED",
                category="connection",
                severity="error",
                message="No cipher suite was negotiated.",
                stage="tls_handshake",
            ),
        )
        state.result["scan_status"] = "failed"
        return False

    state.result.update(
        {
            "tls_version": tls_socket.version(),
            "cipher_suite": cipher[0],
            "cipher_strength": cipher[2],
        }
    )

    return True


def collect_certificate_evidence(
    state: ScanState,
    tls_socket: ssl.SSLSocket,
) -> bool:
    """Collect and parse the peer's certificate evidence."""

    der_certificate = tls_socket.getpeercert(binary_form=True)

    if not der_certificate:
        add_diagnostic(
            state,
            make_diagnostic(
                code="NO_PEER_CERTIFICATE",
                category="certificate",
                severity="error",
                message="The server did not provide a certificate.",
                stage="certificate_collection",
            ),
        )
        state.result["scan_status"] = "failed"
        return False

    try:
        certificate_info = parse_certificate(der_certificate)
    except (ValueError, UnsupportedAlgorithm) as error:
        logger.warning(
            "Certificate parsing failed for %s:%d: %s",
            state.result["target"],
            state.result["port"],
            error,
        )

        add_diagnostic(
            state,
            make_diagnostic(
                code="CERTIFICATE_PARSING_FAILED",
                category="parsing",
                severity="error",
                message=str(error),
                stage="certificate_parsing",
            ),
        )
        state.result["scan_status"] = "partial"
        return False

    state.result.update(certificate_info)
    return True


def collect_key_establishment_evidence(
    state: ScanState,
    target: str,
    port: int,
    timeout: float,
) -> None:
    """Collect key-establishment evidence using a separate TLS handshake."""

    try:
        key_group, key_status = collect_key_establishment_group(
            target,
            port=port,
            timeout=timeout,
        )
    except (OSError, ValueError, TimeoutError) as error:
        logger.warning(
            "Key-establishment probe failed for %s:%d: %s",
            target,
            port,
            error,
        )

        key_group, key_status = None, "unavailable"

        add_diagnostic(
            state,
            make_diagnostic(
                code="KEY_ESTABLISHMENT_PROBE_UNAVAILABLE",
                category="key_establishment",
                severity="warning",
                message=str(error) or "Key-establishment probe failed.",
                stage="key_establishment_probe",
            ),
        )

    state.result["key_establishment_group"] = key_group
    state.result["key_establishment_evidence_status"] = key_status

    state.result["key_establishment_source"] = (
        "openssl_s_client_separate_handshake"
        if key_status == "observed" and key_group
        else None
    )


def scan_tls_connection(
    state: ScanState,
    target: str,
    target_type: TargetType,
    timeout: float,
) -> TLSScanResult:
    """Establish TLS and coordinate evidence collection."""

    port = state.result["port"]

    try:
        resolved: ResolvedTarget = resolve_target(
            target,
            target_type,
            port,
        )
        state.result["resolved_ip_address"] = resolved.ip_address

        context = ssl.create_default_context()

        # Retain the hostname for SNI and certificate identity verification.
        # For IP literals, Python verifies the corresponding IP subjectAltName.
        with socket.create_connection(
            (resolved.ip_address, resolved.port),
            timeout=timeout,
        ) as sock:
            with context.wrap_socket(
                sock,
                server_hostname=resolved.hostname,
            ) as tls_socket:
                state.result["certificate_verification_status"] = "verified"
                state.result["certificate_verification_error"] = None

                if not collect_tls_details(state, tls_socket):
                    return finish_scan(state)

                if not collect_certificate_evidence(state, tls_socket):
                    return finish_scan(state)

                collect_key_establishment_evidence(
                    state,
                    target=resolved.hostname,
                    port=resolved.port,
                    timeout=timeout,
                )

                state.result["scan_status"] = "completed"
                return finish_scan(state)

    except (OSError, ssl.SSLError) as error:
        return handle_connection_error(state, error)


def scan_target(
    target: str,
    port: int = 443,
    timeout: float = 5.0,
) -> TLSScanResult:
    """Scan a DNS hostname or IP address and return collected TLS evidence."""

    # Use safe defaults to ensure invalid input can still produce a
    # canonical result conforming to the TLSScanResult contract.
    result_target = target if isinstance(target, str) else ""
    state = create_scan_state(
        target=result_target,
        target_type="domain",
        port=443,
    )

    try:
        valid_port = validate_port(port)
    except ValueError as error:
        return fail_scan(
            state,
            message=str(error),
            category="input_validation",
            stage="input_validation",
            code="INVALID_SCAN_INPUT",
        )

    state.result["port"] = valid_port

    try:
        valid_timeout = validate_timeout(timeout)
    except ValueError as error:
        return fail_scan(
            state,
            message=str(error),
            category="input_validation",
            stage="input_validation",
            code="INVALID_SCAN_INPUT",
        )

    try:
        target_type, normalized_target = validate_target(target)
    except ValueError as error:
        return fail_scan(
            state,
            message=str(error),
            category="input_validation",
            stage="input_validation",
            code="INVALID_SCAN_INPUT",
        )

    state.result["target_type"] = target_type

    logger.info(
        "Starting TLS scan for target=%s type=%s port=%d",
        result_target,
        target_type,
        valid_port,
    )

    return scan_tls_connection(
        state=state,
        target=normalized_target,
        target_type=target_type,
        timeout=valid_timeout,
    )
