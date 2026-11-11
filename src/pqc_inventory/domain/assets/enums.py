"""Enumerations for cryptographic asset classification and lifecycle."""

from enum import StrEnum


class AssetType(StrEnum):
    """Classify the primary category of a cryptographic asset."""

    COMPUTING_SYSTEM = "computing_system"
    APPLICATION = "application"
    NETWORK_SERVICE = "network_service"
    SOFTWARE_COMPONENT = "software_component"
    CERTIFICATE = "certificate"
    CRYPTOGRAPHIC_KEY_REFERENCE = "cryptographic_key_reference"
    CRYPTOGRAPHIC_MODULE = "cryptographic_module"
    RANDOMNESS_COMPONENT = "randomness_component"
    CRYPTOGRAPHIC_SERVICE = "cryptographic_service"


class AssetLifecycleStatus(StrEnum):
    """Represent the lifecycle status of an asset."""

    UNKNOWN = "unknown"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DECOMMISSIONED = "decommissioned"
