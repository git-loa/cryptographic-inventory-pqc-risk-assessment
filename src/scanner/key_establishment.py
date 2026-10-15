"""
Key-establishment evidence collection using OpenSSL.

This module observes the negotiated key-establishment group from a
separate OpenSSL TLS handshake.

It does not determine whether a server supports every possible
key-establishment mechanism.
"""

import re
import shutil
import subprocess

_GROUP_PATTERNS = (
    re.compile(r"Server Temp Key:\s*([^,\r\n]+)"),
    re.compile(r"Peer Temp Key:\s*([^,\r\n]+)"),
    re.compile(r"Negotiated TLS1\.3 group:\s*([^\r\n]+)"),
)


def parse_key_establishment_group(output: str) -> str | None:
    """
    Extract a negotiated group from recognized OpenSSL output.

    Returns None when the output does not contain a recognized
    group-reporting line.
    """

    for patttern in _GROUP_PATTERNS:
        match = patttern.search(output)

        if match:
            group = match.group(1).strip()

            if group:
                return group
    return None


def collect_key_establishment_group(
    domain: str,
    port: int = 443,
    timeout: int = 5,
) -> tuple[str | None, str]:
    """
    Collect key-establishment evidence using openssl s_client.

    Returns:
        (group, "observed") when a group is found.
        (None, "unavailable") when it cannot be determined.

    This establishes a separate TLS connection from the main scanner.
    """
    openssl_path = shutil.which("openssl")

    if openssl_path is None:
        return "unavailable"

    command = [
        openssl_path,
        "s_client",
        "-connect",
        f"{domain}:{port}",
        "-servername",
        domain,
        "-no-interactive",
    ]

    try:
        completed = subprocess.run(
            command,
            input="",
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    except (OSError, subprocess.TimeoutExpired):
        return None, "unavailable"

    output = completed.stdout + "\n" + completed.stderr

    group = parse_key_establishment_group(output)

    if group is None:
        return None, "unavailable"

    return group, "observed"
