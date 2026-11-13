# Domain Class Design Specification

**Project:** Cryptographic Inventory, Security Assurance and Modernization Framework

**Version:** 0.1.0

**Status:** Proposed

## 1. Purpose

This document describes the Python classes used to represent the framework's domain concepts.

It defines their responsibilities, important attributes and relationships.

The design uses dataclasses, immutable value objects, enumerations and interfaces. Domain classes remain independent of databases, collection tools and external inventory formats.

## 2. Design Principles

The domain design follows these principles:

- Entities have stable UUIDs.
- Value objects are immutable.
- Related objects are combined through composition rather than unnecessary inheritance.
- External references use identifiers rather than complete object copies.
- Shared validation rules are maintained in reusable helpers.
- External data is validated before entering the domain.
- Domain classes do not depend on infrastructure implementations.

## 3. Organization and Inventory

| Class | Responsibility |
|---|---|
| `Organization` | Represents an organization responsible for inventories. |
| `Inventory` | Defines an inventory and its organizational scope. |
| `InventoryMembership` | Records an asset's membership in an inventory. |

An asset may belong to multiple inventories without duplicating its identity.

## 4. Asset Domain

### Asset

**Type:** Entity

Represents an identifiable system, application, service, software component or cryptographic object.

Attributes:

- `asset_id: UUID`
- `asset_type: AssetType`
- `name: str`
- `description: str | None`
- `identifiers: tuple[AssetIdentifier, ...]`
- `specification: AssetSpecification | None`
- `lifecycle: AssetLifecycle`

The asset receives a UUID4 by default.

It validates its identity, classification, identifiers, specification and lifecycle.

A specification is optional because an asset may be discovered before its technical details are known.

### AssetIdentifier

**Type:** Immutable value object

Represents an external identifier associated with an asset.

Attributes:

- `namespace: str`
- `value: str`
- `issuer: str | None`
- `valid_from: datetime | None`
- `valid_until: datetime | None`

The validity timestamps describe how long the identifier is associated with the asset.

### AssetSpecification

**Type:** Union of immutable value objects

Describes technical properties specific to an asset category.

The currently supported specifications are:

| Class | Asset category |
|---|---|
| `NetworkEndpointSpecification` | Network service |
| `CertificateSpecification` | Certificate |
| `SoftwareComponentSpecification` | Software component |
| `CryptographicKeyReferenceSpecification` | Cryptographic key reference |

Additional value objects include:

- `CertificateValidity`: Certificate validity dates.
- `PublicKeyInfo`: Public-key algorithm, optional key size and curve.

The Asset entity checks that a supplied specification matches its asset category.

### AssetLifecycle

**Type:** Immutable value object

Records the current lifecycle state of an asset.

Attributes:

- `status: AssetLifecycleStatus`
- `created_at: datetime`
- `updated_at: datetime`

Lifecycle changes return a new Asset instance while preserving its UUID and creation timestamp.

### AssetRelationship

**Type:** Immutable entity

Represents a directed relationship between two assets.

Attributes:

- `relationship_id: UUID`
- `source_asset_id: UUID`
- `target_asset_id: UUID`
- `relationship_type: RelationshipType`
- `valid_from: datetime | None`
- `valid_until: datetime | None`
- `evidence_references: tuple[UUID, ...]`

It validates its identifiers, relationship type, evidence references and validity period.

It does not contain complete Asset objects.

### RelationshipType

**Type:** String enumeration

Defines the nine supported relationship types:

- `HOSTS`
- `RUNS`
- `EXPOSES`
- `PRESENTS`
- `USES`
- `PROVIDES`
- `DEPENDS_ON`
- `MANAGED_BY`
- `CONTAINS`

Each relationship has a defined direction.

### Relationship Compatibility

The `relationship_rules` module defines which asset categories can participate in each relationship.

`validate_relationship_compatibility()` checks:

- Whether the supplied assets match the relationship's identifiers.
- Whether the source asset category is permitted.
- Whether the target asset category is permitted.

The compatibility rules are maintained internally. The validator is the public interface.

Checking whether referenced assets exist in the inventory and preventing duplicate stored relationships are responsibilities of the inventory application and persistence layers.

### Asset Identity Resolution

**Type:** Application-level capability

Determines whether a discovered asset corresponds to an existing inventory asset.

It considers external identifiers, asset classification and supporting evidence.

Uncertain matches require review rather than automatic merging.

## 5. Evidence Domain

| Class | Responsibility |
|---|---|
| `EvidenceRecord` | Records an observation, demonstrated capability, declaration or derived result. |
| `SubjectReference` | Identifies what the evidence describes. |
| `EvidenceValue` | Holds the typed evidence information. |
| `EvidenceProvenance` | Records where the evidence originated. |

An EvidenceRecord includes its identifier, subject, type, property, value, provenance, observation timestamp, lifecycle status and known limitations.

Evidence is immutable after finalization. New observations create new records.

Evidence may describe assets, organizations, runtimes or collection activities.

## 6. Collection Domain

| Class | Responsibility |
|---|---|
| `CollectionExecution` | Records one collector execution. |
| `CollectionOperation` | Records an individual collection activity. |
| `TLSHandshakeObservation` | Records one actual negotiated TLS connection. |
| `TLSCapabilityProbeResult` | Records the outcome of a controlled TLS capability test. |

A CollectionExecution may contain multiple CollectionOperations.

An operation may produce zero or more evidence records.

TLS handshake observations and controlled capability probes remain separate records.

## 7. Runtime Domain

| Class | Responsibility |
|---|---|
| `RuntimeProfile` | Describes the environment performing collection. |
| `RuntimeCapabilities` | Describes locally available collection and cryptographic capabilities. |
| `LibraryVersion` | Records the version of a relevant library. |

A runtime profile may include the operating system, architecture, Python version, SSL backend and OpenSSL version.

Local capabilities must not be interpreted as remote endpoint capabilities.

## 8. Standards Domain

| Class | Responsibility |
|---|---|
| `StandardsReference` | Identifies an authoritative publication. |
| `StandardsEdition` | Represents a particular publication revision. |
| `StandardsProvision` | Represents an individual requirement or recommendation. |

A StandardsReference may have multiple editions.

Each provision belongs to a specific edition so that previous assessments can retain their original references.

## 9. Assessment Domain

| Class | Responsibility |
|---|---|
| `PolicyIdentity` | Maintains a policy's identity. |
| `PolicyVersion` | Defines a particular policy version. |
| `PolicyRuleIdentity` | Maintains a rule's identity. |
| `PolicyRuleVersion` | Defines a particular version of a rule. |
| `AssessmentContext` | Supplies assets, evidence and assessment configuration. |
| `AssessmentRun` | Records an assessment execution. |
| `PolicyResult` | Records a policy execution result. |
| `AssessmentFinding` | Records an assessment conclusion. |

Each rule version belongs to one policy version.

Every finding identifies its originating rule version, affected assets and supporting evidence.

Assessment policies operate on canonical evidence rather than collector-specific models.

## 10. Risk and Modernization Domain

| Class | Responsibility |
|---|---|
| `RiskAssessment` | Evaluates technical findings against organizational context. |
| `ModernizationPlan` | Coordinates cryptographic modernization activities. |
| `ModernizationTask` | Tracks an individual migration or replacement activity. |

Risk assessments preserve their assumptions and rationale.

Modernization tasks reference affected assets and related findings.

## 11. Shared Types and Validation

### Enumerations

The domain uses controlled enumerations, including:

- `AssetType`
- `AssetLifecycleStatus`
- `RelationshipType`
- `EvidenceType`
- `EvidenceLifecycleStatus`
- `CollectionStatus`
- `PublicationStatus`
- `ProvisionType`
- `PolicyStatus`
- `AssessmentClassification`
- `PolicyExecutionStatus`
- `ModernizationStatus`

Each enumeration is maintained in the module responsible for its domain.

### Validation

Shared validation functions are maintained in the relevant domain validation modules.

They cover common requirements such as:

- Required and optional text.
- Positive integers.
- UUID values.
- Timezone-aware timestamps.
- Valid datetime intervals.

Classes also enforce their own rules, such as specification compatibility, unique identifiers and valid relationship classifications.

## 12. Interfaces and External Data

Application components communicate through defined interfaces, using Python `Protocol` where appropriate.

Important interfaces include:

| Protocol | Responsibility |
|---|---|
| `Collector` | Performs collection activities. |
| `AssetRepository` | Retrieves and stores assets. |
| `EvidenceRepository` | Retrieves and stores evidence. |
| `InventoryRepository` | Manages inventory records. |
| `AssessmentPolicy` | Evaluates assessment context. |
| `PolicyRegistry` | Resolves policy versions. |
| `StandardsRepository` | Retrieves standards and provisions. |
| `BOMImporter` | Imports external inventory documents. |
| `BOMExporter` | Exports inventory documents. |

External data is validated and converted into domain objects through the appropriate application or adapter boundary.

Serialization and database-specific representations remain outside the domain classes.

**Guiding principle:** Each class represents one clear responsibility. Related objects are composed, references use identifiers, and shared rules are implemented once.
