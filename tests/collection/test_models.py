"""Tests for TLS collection data models and their contracts."""

from typing import get_args, get_type_hints

from src.collection import models

# ---------------------------------------------------------------------------
# Schema version
# ---------------------------------------------------------------------------


def test_scan_schema_version():
    """The collection schema should expose the expected version."""
    assert models.SCAN_SCHEMA_VERSION == "1.0"


# ---------------------------------------------------------------------------
# Literal contracts
# ---------------------------------------------------------------------------


def test_target_type_values():
    """Target types should represent supported network target categories."""
    assert get_args(models.TargetType) == ("domain", "ipv4", "ipv6")


def test_scan_status_values():
    """Scan status should distinguish completed, partial, and failed scans."""
    assert get_args(models.ScanStatus) == ("completed", "partial", "failed")


def test_key_establishment_evidence_status_values():
    """Key-establishment evidence should have explicit collection states."""
    assert get_args(models.KeyEstablishmentEvidenceStatus) == (
        "observed",
        "unavailable",
        "not_attempted",
    )


def test_certificate_verification_status_values():
    """Certificate verification should distinguish its supported outcomes."""
    assert get_args(models.CertificateVerificationStatus) == (
        "verified",
        "failed",
        "not_performed",
        "unknown",
    )


def test_diagnostic_severity_values():
    """Diagnostic severity should use the established severity levels."""
    assert get_args(models.DiagnosticSeverity) == ("info", "warning", "error")


def test_diagnostic_category_values():
    """Diagnostic categories should identify the source of a scan issue."""
    assert get_args(models.DiagnosticCategory) == (
        "input_validation",
        "connection",
        "timeout",
        "certificate",
        "key_establishment",
        "parsing",
        "internal",
    )


# ---------------------------------------------------------------------------
# ScanDiagnostic contract
# ---------------------------------------------------------------------------


def test_scan_diagnostic_required_fields():
    """Every diagnostic should declare all required fields."""
    annotations = get_type_hints(models.ScanDiagnostic)

    assert set(annotations) == {
        "code",
        "category",
        "severity",
        "message",
        "stage",
    }


def test_scan_diagnostic_accepts_expected_structure():
    """A diagnostic should be representable using the declared data contract."""
    diagnostic: models.ScanDiagnostic = {
        "code": "TLS_CONNECTION_FAILED",
        "category": "connection",
        "severity": "error",
        "message": "The TLS connection could not be established.",
        "stage": "connection",
    }

    assert diagnostic["code"] == "TLS_CONNECTION_FAILED"
    assert diagnostic["category"] == "connection"
    assert diagnostic["severity"] == "error"
    assert diagnostic["stage"] == "connection"


# ---------------------------------------------------------------------------
# TLSScanResult required and optional fields
# ---------------------------------------------------------------------------


def test_tls_scan_result_required_fields():
    """TLSScanResult should declare all required scan fields."""
    required_keys = getattr(
        models.TLSScanResult,
        "__required_keys__",
    )

    expected_fields = {
        "schema_version",
        "scan_id",
        "target",
        "target_type",
        "port",
        "resolved_ip_address",
        "scan_status",
        "started_at",
        "completed_at",
        "scan_time_seconds",
        "certificate_verification_status",
        "certificate_verification_error",
        "key_establishment_evidence_status",
        "diagnostics",
    }

    assert expected_fields == set(required_keys)


def test_tls_scan_result_optional_fields():
    """TLSScanResult should declare its optional evidence fields."""
    optional_keys = getattr(
        models.TLSScanResult,
        "__optional_keys__",
    )

    expected_fields = {
        "tls_version",
        "cipher_suite",
        "cipher_strength",
        "certificate_version",
        "certificate_serial_number",
        "certificate_subject",
        "certificate_issuer",
        "not_before",
        "not_after",
        "public_key_algorithm",
        "public_key_variant",
        "public_key_algorithm_oid",
        "key_size",
        "public_key_curve",
        "rsa_public_exponent",
        "certificate_signature_algorithm_oid",
        "certificate_signature_hash_algorithm",
        "san_dns_names",
        "san_ip_addresses",
        "key_usage",
        "extended_key_usage",
        "basic_constraints",
        "key_establishment_group",
        "key_establishment_source",
    }

    assert expected_fields == set(optional_keys)


def test_tls_scan_result_required_annotations():
    """Required scan fields should have the expected declared annotations."""
    annotations = get_type_hints(models.TLSScanResult)

    assert annotations["schema_version"] is str
    assert annotations["scan_id"] is str
    assert annotations["target"] is str
    assert annotations["port"] is int
    assert annotations["scan_time_seconds"] is float
    assert annotations["diagnostics"] == list[models.ScanDiagnostic]


# ---------------------------------------------------------------------------
# TLSScanResult examples
# ---------------------------------------------------------------------------


def test_tls_scan_result_supports_minimal_result():
    """A result can contain required fields without optional evidence."""
    result: models.TLSScanResult = {
        "schema_version": models.SCAN_SCHEMA_VERSION,
        "scan_id": "test-scan-001",
        "target": "example.com",
        "target_type": "domain",
        "port": 443,
        "resolved_ip_address": None,
        "scan_status": "failed",
        "started_at": "2026-01-01T12:00:00+00:00",
        "completed_at": None,
        "scan_time_seconds": 0.5,
        "certificate_verification_status": "unknown",
        "certificate_verification_error": None,
        "key_establishment_evidence_status": "not_attempted",
        "diagnostics": [],
    }

    assert result["schema_version"] == models.SCAN_SCHEMA_VERSION
    assert result["scan_status"] == "failed"
    assert result["resolved_ip_address"] is None
    assert result["completed_at"] is None
    assert result["diagnostics"] == []

    assert "tls_version" not in result
    assert "public_key_algorithm" not in result
    assert "key_establishment_group" not in result


def test_tls_scan_result_supports_collected_evidence():
    """A result can include TLS, certificate, and key-establishment evidence."""
    result: models.TLSScanResult = {
        "schema_version": models.SCAN_SCHEMA_VERSION,
        "scan_id": "test-scan-002",
        "target": "example.com",
        "target_type": "domain",
        "port": 443,
        "resolved_ip_address": "192.0.2.10",
        "scan_status": "completed",
        "started_at": "2026-01-01T12:00:00+00:00",
        "completed_at": "2026-01-01T12:00:01+00:00",
        "scan_time_seconds": 1.0,
        "certificate_verification_status": "verified",
        "certificate_verification_error": None,
        "key_establishment_evidence_status": "observed",
        "diagnostics": [],
        "tls_version": "TLSv1.3",
        "cipher_suite": "TLS_AES_128_GCM_SHA256",
        "public_key_algorithm": "RSA",
        "key_size": 2048,
        "key_establishment_group": "X25519",
        "key_establishment_source": "openssl",
    }

    assert result["scan_status"] == "completed"
    assert result["tls_version"] == "TLSv1.3"
    assert result["public_key_algorithm"] == "RSA"
    assert result["key_size"] == 2048
    assert result["key_establishment_group"] == "X25519"
    assert result["key_establishment_evidence_status"] == "observed"
