# Domain Class Design Specification

**Project:** Cryptographic Inventory, Security Assurance and Modernization Framework

**Version:** 0.1.0

**Status:** Proposed

## 1. Purpose

This document translates the domain model and entity relationship specifications into an implementation-oriented Python class design.

It defines:

- Class responsibilities.
- Entity and value-object distinctions.
- Attributes and data types.
- Object composition.
- Interface requirements.
- Immutability.
- Serialization boundaries.

The design targets Python 3.12 and later.

## 2. Implementation Principles

The domain implementation follows these principles:

1. Use dataclasses for domain entities and value objects.
2. Use immutable dataclasses for finalized evidence and historical assessment objects.
3. Use enums for controlled domain values.
4. Use protocols for collection and assessment interfaces.
5. Use Pydantic at external validation boundaries.
6. Use composition rather than unnecessary inheritance.
7. Keep domain objects independent of storage and serialization technologies.
8. Use UUIDs for internal entity identification.
9. Use timezone-aware UTC timestamps.
10. Preserve historical evidence and assessment versions.

Recommended Python features include:

- Type annotations.
- Dataclasses.
- Enums.
- UUID.
- Datetime.
- Generic types where justified.
- Structural typing through Protocol.

## 3. Organization and Inventory Models

### 3.1 Organization

**Type:** Entity

**Responsibility:** Represents the organization responsible for one or more cryptographic inventories.

Proposed attributes:

| Attribute | Type |
|---|---|
| organization_id | UUID |
| name | str |
| description | str or None |
| created_at | datetime |

### 3.2 Inventory

**Type:** Entity

**Responsibility:** Defines an organizational inventory scope.

Proposed attributes:

| Attribute | Type |
|---|---|
| inventory_id | UUID |
| organization_id | UUID |
| name | str |
| description | str or None |
| created_at | datetime |
| status | InventoryStatus |

### 3.3 InventoryMembership

**Type:** Entity or versioned association record.

**Responsibility:** Associates an asset with an inventory while preserving membership history.

Proposed attributes:

| Attribute | Type |
|---|---|
| membership_id | UUID |
| inventory_id | UUID |
| asset_id | UUID |
| valid_from | datetime |
| valid_until | datetime or None |

Membership history must not require duplicating an asset.

## 4. Asset Models

### 4.1 CryptographicAsset

**Type:** Entity

**Responsibility:** Maintains the identity and lifecycle of a discovered cryptographic asset.

Proposed attributes:

| Attribute | Type |
|---|---|
| asset_id | UUID |
| asset_type | AssetType |
| name | str |
| description | str or None |
| identifiers | tuple[AssetIdentifier, ...] |
| specification | AssetSpecification |
| lifecycle_status | AssetLifecycleStatus |
| created_at | datetime |
| updated_at | datetime |

Organizational ownership is represented through inventory membership or explicit organizational relationships.

### 4.2 AssetIdentifier

**Type:** Immutable value object.

**Responsibility:** Represents an external identifier associated with an asset.

Attributes:

- namespace
- value
- issuer
- valid_from
- valid_until

Identifiers must preserve their namespace to avoid confusing different identification systems.

### 4.3 AssetSpecification

**Type:** Typed value object family.

**Responsibility:** Holds attributes specific to an asset category.

Initial specifications:

- NetworkEndpointSpecification.
- CertificateSpecification.
- SoftwareComponentSpecification.
- CryptographicKeySpecification.
- CryptographicModuleSpecification.
- RandomnessComponentSpecification.

We will introduce specialized specifications only when collection requirements justify them.

### 4.4 AssetRelationship

**Type:** Entity.

**Responsibility:** Represents a directed relationship between two assets.

Attributes:

- relationship_id
- source_asset_id
- target_asset_id
- relationship_type
- valid_from
- valid_until
- supporting_evidence_references

Relationships must be independently traceable.

## 5. Evidence Models

### 5.1 EvidenceRecord

**Type:** Immutable entity.

**Responsibility:** Represents a finalized observation, declared property, demonstrated capability or derived conclusion.

Attributes:

- evidence_id
- subject_asset_id
- evidence_type
- property
- value
- status
- provenance
- observed_at
- limitations

Evidence values must be semantically typed.

Arbitrary unvalidated dictionaries should not become the default domain representation.

### 5.2 EvidenceProvenance

**Type:** Immutable value object.

**Responsibility:** Identifies the origin and collection history of evidence.

Attributes:

- source_type
- source_identifier
- collection_execution_id
- runtime_id
- collection_method
- timestamp

Imported or declared evidence may not have a collection execution.

### 5.3 EvidenceReference

**Type:** Immutable value object.

**Responsibility:** Provides a stable reference to an existing evidence record.

It should contain:

- evidence_id
- optional property reference

References must not duplicate complete evidence payloads.

## 6. Collection Models

### 6.1 CollectionExecution

**Type:** Entity.

**Responsibility:** Represents one collector execution.

Attributes:

- execution_id
- collector_id
- collector_version
- runtime_id
- started_at
- completed_at
- status
- diagnostics

One execution may produce multiple evidence records.

### 6.2 CollectionOperation

**Type:** Child entity within a collection execution.

**Responsibility:** Represents an individual collection activity.

Attributes:

- operation_id
- execution_id
- operation_type
- target_reference
- started_at
- completed_at
- status
- diagnostics

Individual TLS handshakes and controlled probes may be represented as specialized operation payloads.

### 6.3 TLSHandshakeObservation

**Type:** Immutable typed value object.

**Responsibility:** Represents the result of one TLS handshake.

Attributes:

- connection_id
- target_reference
- protocol_version
- cipher_suite
- negotiated_group
- peer_certificate_reference
- certificate_verification
- timestamp

Every negotiated property must originate from the same handshake.

### 6.4 TLSCapabilityProbeResult

**Type:** Immutable typed value object.

**Responsibility:** Represents one controlled TLS capability probe.

Attributes:

- probe_id
- requested_protocol
- requested_group
- client_configuration
- outcome
- diagnostic
- runtime_reference

A probe result must preserve the limitations of the probing client.

## 7. Runtime Models

### 7.1 RuntimeProfile

**Type:** Immutable entity or versioned snapshot.

**Responsibility:** Describes the collection execution environment.

Attributes:

- runtime_id
- operating_system
- architecture
- python_implementation
- python_version
- ssl_backend
- openssl_version
- library_versions
- capabilities
- captured_at

### 7.2 RuntimeCapabilities

**Type:** Immutable value object.

**Responsibility:** Describes capabilities available to the collection runtime.

Attributes should include:

- negotiated_group_api
- configurable_groups_api
- available_tls_versions
- locally_available_groups
- certificate_validation_support
- available_collection_methods

Runtime capabilities must not be interpreted as remote endpoint capabilities.

## 8. Standards Models

### 8.1 StandardsReference

**Type:** Entity.

**Responsibility:** Maintains the stable identity of a standards publication.

Attributes:

- reference_id
- publisher
- document_identifier
- title

### 8.2 StandardsEdition

**Type:** Immutable entity.

**Responsibility:** Represents a particular publication revision.

Attributes:

- edition_id
- reference_id
- revision
- publication_date
- effective_date
- publication_status
- official_url
- supersedes

### 8.3 StandardsProvision

**Type:** Immutable value object owned by a standards edition.

Attributes:

- provision_id
- section
- title
- provision_type
- requirement_summary
- applicability

A provision must identify its originating standards edition.

## 9. Assessment Models

### 9.1 PolicyIdentity

**Type:** Entity.

**Responsibility:** Represents the permanent identity of an assessment policy.

Attributes:

- policy_id
- policy_name
- created_at

### 9.2 PolicyVersion

**Type:** Immutable entity.

**Responsibility:** Represents one version of a policy specification.

Attributes:

- policy_version_id
- policy_id
- version
- objective
- scope
- exclusions
- effective_from
- status

### 9.3 PolicyRuleIdentity

**Type:** Entity.

**Responsibility:** Maintains the stable identity of an assessment rule.

Attributes:

- rule_id
- policy_id
- name

### 9.4 PolicyRuleVersion

**Type:** Immutable entity.

**Responsibility:** Defines one version of an assessment rule.

Attributes:

- rule_version_id
- rule_id
- policy_version_id
- version
- required_evidence
- rationale
- standards_provisions

Evaluation logic belongs to the assessment implementation and must not be represented as arbitrary executable data.

### 9.5 AssessmentContext

**Type:** Immutable value object.

**Responsibility:** Supplies the assets, evidence and configuration necessary for assessment.

Attributes:

- scope
- asset_references
- evidence_references
- selected_policy_versions
- standards_profile
- organizational_context
- assessment_timestamp

It must remain independent of collector-specific result classes.

### 9.6 AssessmentRun

**Type:** Immutable entity.

**Responsibility:** Represents one complete assessment execution.

Attributes:

- assessment_run_id
- created_at
- scope
- methodology_version
- policy_version_snapshots
- standards_edition_references
- evidence_references
- runtime_references

### 9.7 PolicyResult

**Type:** Immutable child entity.

**Responsibility:** Records the execution result of one policy.

Attributes:

- policy_version_id
- execution_status
- finding_references
- limitations
- diagnostics

### 9.8 AssessmentFinding

**Type:** Immutable entity.

**Responsibility:** Records an individual policy conclusion.

Attributes:

- finding_id
- affected_asset_references
- policy_id
- policy_version_id
- rule_id
- rule_version_id
- classification
- rationale
- evidence_references
- standards_provision_references
- limitations

Every finding must remain traceable to its exact rule version and supporting evidence.

## 10. Risk Models

### 10.1 RiskAssessment

**Type:** Entity.

**Responsibility:** Evaluates technical findings against organizational context.

Attributes:

- risk_id
- affected_assets
- related_findings
- business_context
- exposure_rationale
- impact_basis
- likelihood_basis
- priority
- recommendations

Risk scoring requires a separately validated methodology.

### 10.2 ModernizationPlan

**Type:** Entity.

**Responsibility:** Coordinates cryptographic replacement and modernization activities.

Attributes:

- plan_id
- affected_assets
- related_findings
- proposed_replacements
- activities
- validation_requirements
- status
- residual_risk_references

## 11. Dataclasses, Enums and Protocols

### Dataclasses

Dataclasses are the preferred implementation mechanism for domain entities and value objects.

Use frozen dataclasses for finalized evidence, runtime snapshots, standards editions and historical assessment records.

Use mutable dataclasses only for entities with explicitly controlled state transitions.

### Enums

Enums should represent stable controlled values such as:

- AssetType.
- AssetLifecycleStatus.
- EvidenceType.
- EvidenceStatus.
- CollectionStatus.
- RelationshipType.
- PublicationStatus.
- AssessmentClassification.
- PolicyExecutionStatus.

Existing classification values should be preserved during the initial migration and reviewed separately.

### Protocols

Protocols should define collection and assessment contracts.

Proposed interfaces:

- Collector.
- AssetResolver.
- EvidenceRepository.
- InventoryRepository.
- AssessmentPolicy.
- PolicyRegistry.
- StandardsRepository.
- BOMImporter.
- BOMExporter.

### Pydantic

Pydantic should primarily validate external inputs and data contracts.

It should not become a mandatory dependency of every domain object.

## 12. Serialization and Persistence

Domain objects must not serialize themselves directly into CycloneDX structures.

Dedicated adapters should convert domain objects into:

- Native JSON evidence records.
- Assessment persistence records.
- CycloneDX CBOM documents.
- External API representations.

Deserialization must validate schema versions and reject unsupported or malformed structures appropriately.

## 13. Python Compatibility

The initial implementation must support Python 3.12 and Python 3.15.2.

It should use stable language features available in Python 3.12.

Runtime capability detection should determine which TLS and cryptographic operations are available.

Python version comparisons must not replace actual capability detection.

## 14. Initial Implementation Priorities

The first model implementation should focus on:

1. Asset identifiers and cryptographic assets.
2. Evidence records and provenance.
3. Collection execution and operations.
4. Runtime profiles and capabilities.
5. Assessment contexts and findings.
6. Policy and standards versioning.

Risk, modernization and organizational integration models will follow when their requirements are defined.

**Guiding principle:** Domain classes represent stable concepts and responsibilities. External validation, persistence and interoperability must remain separate from those concepts.
