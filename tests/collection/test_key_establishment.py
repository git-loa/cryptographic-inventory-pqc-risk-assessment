from unittest.mock import patch

from src.collection.key_establishment import (
    collect_key_establishment_group,
    parse_key_establishment_group,
)


def test_parse_server_temp_key():
    output = """
    Server Temp Key: X25519, 253 bits
    """

    assert parse_key_establishment_group(output) == "X25519"


def test_parse_peer_temp_key():
    output = """
    Peer Temp Key: secp256r1, 256 bits
    """

    assert parse_key_establishment_group(output) == "secp256r1"


def test_parse_negotiated_tls13_group():
    output = """
    Negotiated TLS1.3 group: X25519
    """

    assert parse_key_establishment_group(output) == "X25519"


def test_unknown_output_returns_none():
    output = """
    New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384
    """

    assert parse_key_establishment_group(output) is None


def test_empty_output_returns_none():
    assert parse_key_establishment_group("") is None


def test_missing_openssl_returns_unavailable():
    with patch(
        "src.collection.key_establishment.shutil.which",
        return_value=None,
    ):
        result = collect_key_establishment_group("example.com")

    assert result == (None, "unavailable")
