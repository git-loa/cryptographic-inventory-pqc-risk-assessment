"""Tests for OpenSSL key-establishment evidence collection."""

import subprocess
from unittest.mock import Mock

from pqc_inventory.collection import key_establishment

# ---------------------------------------------------------
# Tests for parse_key_establishment_group()
# ---------------------------------------------------------


def test_parse_server_temp_key():
    output = "Server Temp Key: X25519, 253 bits"

    result = key_establishment.parse_key_establishment_group(output)

    assert result == "X25519"


def test_parse_peer_temp_key():
    output = "Peer Temp Key: ECDH, secp256r1, 256 bits"

    result = key_establishment.parse_key_establishment_group(output)

    assert result == "ECDH"


def test_parse_negotiated_tls13_group():
    output = "Negotiated TLS1.3 group: X25519"

    result = key_establishment.parse_key_establishment_group(output)

    assert result == "X25519"


def test_parse_group_with_surrounding_whitespace():
    output = "Server Temp Key:   X25519   , 253 bits"

    result = key_establishment.parse_key_establishment_group(output)

    assert result == "X25519"


def test_parse_group_returns_none_when_output_is_unrecognized():
    output = "CONNECTED\nTLS handshake completed successfully."

    result = key_establishment.parse_key_establishment_group(output)

    assert result is None


def test_parse_group_returns_none_for_empty_output():
    result = key_establishment.parse_key_establishment_group("")

    assert result is None


# ---------------------------------------------------------
# Tests for collect_key_establishment_group()
# ---------------------------------------------------------


def test_collection_returns_unavailable_when_openssl_is_missing(
    monkeypatch,
):
    monkeypatch.setattr(
        key_establishment.shutil,
        "which",
        lambda _: None,
    )

    result = key_establishment.collect_key_establishment_group(
        "example.com",
        port=443,
        timeout=5,
    )

    assert result == (None, "unavailable")


def test_collection_returns_observed_group_from_openssl(
    monkeypatch,
):
    monkeypatch.setattr(
        key_establishment.shutil,
        "which",
        lambda _: "openssl",
    )

    completed = subprocess.CompletedProcess(
        args=["openssl"],
        returncode=0,
        stdout="",
        stderr="Server Temp Key: X25519, 253 bits",
    )

    run_mock = Mock(return_value=completed)

    monkeypatch.setattr(
        key_establishment.subprocess,
        "run",
        run_mock,
    )

    result = key_establishment.collect_key_establishment_group(
        "example.com",
        port=443,
        timeout=5,
    )

    assert result == ("X25519", "observed")

    run_mock.assert_called_once()

    command = run_mock.call_args.args[0]

    assert command[0] == "openssl"
    assert command[1] == "s_client"
    assert "-connect" in command
    assert "example.com:443" in command
    assert "-servername" in command
    assert "example.com" in command
    assert "-no-interactive" in command

    assert run_mock.call_args.kwargs["timeout"] == 5
    assert run_mock.call_args.kwargs["capture_output"] is True
    assert run_mock.call_args.kwargs["text"] is True


def test_collection_returns_unavailable_when_group_is_not_reported(
    monkeypatch,
):
    monkeypatch.setattr(
        key_establishment.shutil,
        "which",
        lambda _: "openssl",
    )

    completed = subprocess.CompletedProcess(
        args=["openssl"],
        returncode=0,
        stdout="CONNECTED\n",
        stderr="TLS handshake completed.",
    )

    monkeypatch.setattr(
        key_establishment.subprocess,
        "run",
        Mock(return_value=completed),
    )

    result = key_establishment.collect_key_establishment_group(
        "example.com",
    )

    assert result == (None, "unavailable")


def test_collection_returns_unavailable_when_openssl_times_out(
    monkeypatch,
):
    monkeypatch.setattr(
        key_establishment.shutil,
        "which",
        lambda _: "openssl",
    )

    monkeypatch.setattr(
        key_establishment.subprocess,
        "run",
        Mock(
            side_effect=subprocess.TimeoutExpired(
                cmd="openssl",
                timeout=5,
            )
        ),
    )

    result = key_establishment.collect_key_establishment_group(
        "example.com",
        timeout=5,
    )

    assert result == (None, "unavailable")


def test_collection_returns_unavailable_when_process_cannot_start(
    monkeypatch,
):
    monkeypatch.setattr(
        key_establishment.shutil,
        "which",
        lambda _: "openssl",
    )

    monkeypatch.setattr(
        key_establishment.subprocess,
        "run",
        Mock(side_effect=OSError("Unable to start OpenSSL")),
    )

    result = key_establishment.collect_key_establishment_group(
        "example.com",
    )

    assert result == (None, "unavailable")
