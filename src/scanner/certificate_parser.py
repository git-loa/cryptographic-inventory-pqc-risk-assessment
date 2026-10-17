"""Extract structured metadata from X.509 certificates."""

from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import (
    dsa,
    ec,
    ed25519,
    ed448,
    rsa,
)


def _extract_public_key_info(public_key: Any) -> dict[str, Any]:
    """Extract the public-key algorithm and algorithm-specific parameters."""
    info: dict[str, Any] = {
        "public_key_algorithm": type(public_key).__name__,
        "key_size": getattr(public_key, "key_size", None),
        "public_key_curve": None,
        "rsa_public_exponent": None,
    }

    if isinstance(public_key, rsa.RSAPublicKey):
        info["public_key_algorithm"] = "RSA"
        info["rsa_public_exponent"] = public_key.public_numbers().e

    elif isinstance(public_key, ec.EllipticCurvePublicKey):
        info["public_key_algorithm"] = "EC"
        info["public_key_curve"] = public_key.curve.name

    elif isinstance(public_key, dsa.DSAPublicKey):
        info["public_key_algorithm"] = "DSA"

    elif isinstance(public_key, ed25519.Ed25519PublicKey):
        info["public_key_algorithm"] = "Ed25519"
        info["key_size"] = None

    elif isinstance(public_key, ed448.Ed448PublicKey):
        info["public_key_algorithm"] = "Ed448"
        info["key_size"] = None

    return info


def _extract_name(name: x509.Name) -> dict[str, str]:
    """Convert an X.509 name into a mapping of attribute OIDs to values."""
    return {attribute.oid.dotted_string: attribute.value for attribute in name}


def _extract_san(cert: x509.Certificate) -> dict[str, list[str]]:
    """Extract DNS and IP addresses from the Subject Alternative Name extension."""
    result = {"san_dns_names": [], "san_ip_addresses": []}

    try:
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    except x509.ExtensionNotFound:
        return result

    result["san_dns_names"] = san.get_values_for_type(x509.DNSName)
    result["san_ip_addresses"] = [
        str(address) for address in san.get_values_for_type(x509.IPAddress)
    ]

    return result


def _extract_key_usage(cert: x509.Certificate) -> dict[str, Any]:
    """Extract Key Usage and Extended Key Usage extension values."""
    try:
        usage = cert.extensions.get_extension_for_class(x509.KeyUsage).value
        key_usage = {
            "digital_signature": usage.digital_signature,
            "content_commitment": usage.content_commitment,
            "key_encipherment": usage.key_encipherment,
            "data_encipherment": usage.data_encipherment,
            "key_agreement": usage.key_agreement,
            "key_cert_sign": usage.key_cert_sign,
            "crl_sign": usage.crl_sign,
        }
    except x509.ExtensionNotFound:
        key_usage = None

    try:
        extended_usage = cert.extensions.get_extension_for_class(
            x509.ExtendedKeyUsage
        ).value
        extended_key_usage = [oid.dotted_string for oid in extended_usage]
    except x509.ExtensionNotFound:
        extended_key_usage = None

    return {
        "key_usage": key_usage,
        "extended_key_usage": extended_key_usage,
    }


def _extract_basic_constraints(
    cert: x509.Certificate,
) -> dict[str, Any] | None:
    """Extract the certificate authority flag and path-length constraint."""
    try:
        constraints = cert.extensions.get_extension_for_class(
            x509.BasicConstraints
        ).value
    except x509.ExtensionNotFound:
        return None

    return {
        "ca": constraints.ca,
        "path_length": constraints.path_length,
    }


def _extract_signature_info(cert: x509.Certificate) -> dict[str, Any]:
    """Extract the certificate signature algorithm and hash algorithm."""
    hash_algorithm = cert.signature_hash_algorithm

    return {
        "certificate_signature_algorithm_oid": (
            cert.signature_algorithm_oid.dotted_string
        ),
        "certificate_signature_hash_algorithm": (
            hash_algorithm.name if hash_algorithm is not None else None
        ),
    }


def parse_certificate(der_cert: bytes) -> dict[str, Any]:
    """Parse a DER-encoded certificate into structured inventory metadata.

    This function extracts certificate fields for inventory and assessment.
    It does not independently establish certificate trust or hostname validity.

    Args:
        der_cert: The certificate encoded using Distinguished Encoding Rules.

    Returns:
        A dictionary containing certificate identity, validity, public-key,
        signature, SAN, usage, and basic-constraint metadata.

    Raises:
        ValueError: If the supplied DER data cannot be parsed as a certificate.
    """
    cert = x509.load_der_x509_certificate(der_cert)
    public_key_info = _extract_public_key_info(cert.public_key())

    result = {
        "certificate_version": cert.version.name,
        "certificate_serial_number": str(cert.serial_number),
        "certificate_subject": _extract_name(cert.subject),
        "certificate_issuer": _extract_name(cert.issuer),
        "not_before": cert.not_valid_before_utc.isoformat(),
        "not_after": cert.not_valid_after_utc.isoformat(),
    }

    result.update(public_key_info)
    result.update(_extract_signature_info(cert))
    result.update(_extract_san(cert))
    result.update(_extract_key_usage(cert))
    result["basic_constraints"] = _extract_basic_constraints(cert)

    return result
