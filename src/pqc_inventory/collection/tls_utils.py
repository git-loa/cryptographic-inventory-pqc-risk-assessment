"""Shared target, timestamp, and diagnostic utilities for TLS collection."""

from __future__ import annotations

import ipaddress
import math
import socket
from dataclasses import dataclass
from datetime import datetime, timezone

from pqc_inventory.collection.models import (
    DiagnosticCategory,
    DiagnosticSeverity,
    ScanDiagnostic,
    TargetType,
)


@dataclass(frozen=True, slots=True)
class ResolvedTarget:
    """Represent a validated target and its selected network address."""

    hostname: str
    ip_address: str
    port: int


def utc_now() -> str:
    """Return the current UTC time as an ISO 8601 timestamp."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_target(target: str) -> tuple[TargetType, str]:
    """Validate and classify an IP address or DNS hostname."""

    if not isinstance(target, str):
        raise ValueError("Target must be a string.")

    target = target.strip()

    if not target:
        raise ValueError("Target must not be empty.")

    try:
        address = ipaddress.ip_address(target)
    except ValueError:
        address = None

    if isinstance(address, ipaddress.IPv4Address):
        return "ipv4", str(address)

    if isinstance(address, ipaddress.IPv6Address):
        return "ipv6", str(address)

    hostname = target[:-1] if target.endswith(".") else target

    if not hostname or len(hostname) > 253:
        raise ValueError("Invalid DNS hostname.")

    try:
        ascii_hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError as error:
        raise ValueError("Invalid DNS hostname.") from error

    labels = ascii_hostname.split(".")

    if len(labels) < 2:
        raise ValueError("Hostname must contain at least two labels.")

    for label in labels:
        if not label or len(label) > 63:
            raise ValueError("Invalid DNS hostname label.")

        if label.startswith("-") or label.endswith("-"):
            raise ValueError("Invalid DNS hostname label.")

        if not all(character.isalnum() or character == "-" for character in label):
            raise ValueError("Invalid character in DNS hostname.")

    return "domain", ascii_hostname.lower()


def validate_port(port: int) -> int:
    """Validate a TCP port number."""

    if isinstance(port, bool) or not isinstance(port, int):
        raise ValueError("Port must be an integer.")

    if not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535.")

    return port


def validate_timeout(timeout: float) -> float:
    """Validate a positive, finite connection timeout."""

    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise ValueError("Timeout must be a number.")

    timeout = float(timeout)

    if not math.isfinite(timeout) or not 0 < timeout <= 300:
        raise ValueError("Timeout must be greater than 0 and at most 300 seconds.")

    return timeout


def make_diagnostic(
    code: str,
    category: DiagnosticCategory,
    severity: DiagnosticSeverity,
    message: str,
    stage: str,
) -> ScanDiagnostic:
    """Create a structured collection diagnostic."""

    return {
        "code": code,
        "category": category,
        "severity": severity,
        "message": message,
        "stage": stage,
    }


def resolve_target(
    target: str,
    target_type: TargetType,
    port: int,
) -> ResolvedTarget:
    """Resolve a validated target to an IP address and TCP port."""

    validate_port(port)

    if target_type in ("ipv4", "ipv6"):
        address = ipaddress.ip_address(target)

        if target_type == "ipv4" and not isinstance(address, ipaddress.IPv4Address):
            raise ValueError("Target type does not match the IP address.")

        if target_type == "ipv6" and not isinstance(address, ipaddress.IPv6Address):
            raise ValueError("Target type does not match the IP address.")

        normalized_ip = str(address)

        return ResolvedTarget(
            hostname=normalized_ip,
            ip_address=normalized_ip,
            port=port,
        )

    if target_type != "domain":
        raise ValueError("Unsupported target type.")

    addresses = socket.getaddrinfo(
        target,
        port,
        type=socket.SOCK_STREAM,
    )

    if not addresses:
        raise socket.gaierror("Hostname resolution returned no addresses.")

    sockaddr = addresses[0][4]
    resolved_ip = str(ipaddress.ip_address(sockaddr[0]))

    return ResolvedTarget(
        hostname=target,
        ip_address=resolved_ip,
        port=port,
    )
