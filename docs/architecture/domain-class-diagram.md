# Domain Class Diagram Specification

**Project:** Cryptographic Inventory, Security Assurance and Modernization Framework

**Version:** 0.1.0

**Status:** Proposed

## 1. Purpose

This document defines the proposed Python domain classes, their attributes, responsibilities, composition and relationships.

The class design follows the approved domain model, entity relationship specification and domain model consistency decisions.

It is independent of database technology, CycloneDX implementation and external serialization formats.

## 2. Class Design Principles

1. Entities have independent identities.
2. Value objects represent descriptive information without independent identity.
3. Composition is preferred over unnecessary inheritance.
4. Historical evidence and assessment snapshots are immutable.
5. Domain entities reference separate aggregates through identifiers.
6. Interfaces use structural typing through Protocol.
7. External data validation occurs at system boundaries.
8. Domain objects remain independent of collectors and storage implementations.

## 3. Organization and Inventory

```mermaid
classDiagram
    class Organization {
        +UUID organization_id
        +str name
        +str description
        +datetime created_at
    }

    class Inventory {
        +UUID inventory_id
        +UUID organization_id
        +str name
        +InventoryStatus status
        +datetime created_at
    }

    class InventoryMembership {
        +UUID membership_id
        +UUID inventory_id
        +UUID asset_id
        +datetime valid_from
        +datetime valid_until
    }

    Organization "1" --> "0..*" Inventory : maintains
    Inventory "1" --> "0..*" InventoryMembership : contains
    InventoryMembership "*" --> "1" Asset : references
```

### Responsibilities

**Organization**

Maintains organizational identity and ownership boundaries.

**Inventory**

Defines the organizational scope of asset discovery and assessment.

**InventoryMembership**

Records an asset's participation in an inventory without duplicating the asset.

## 4. Asset Domain

```mermaid
classDiagram
    class Asset {
        +UUID asset_id
        +AssetType asset_type
        +str name
        +str description
        +AssetLifecycleStatus lifecycle_status
        +datetime created_at
        +datetime updated_at
    }

    class AssetIdentifier {
        +str namespace
        +str value
        +str issuer
        +datetime valid_from
        +datetime valid_until
    }

    class AssetSpecification {
        <<Protocol>>
    }

    class AssetRelationship {
        +UUID relationship_id
        +UUID source_asset_id
        +UUID target_asset_id
        +RelationshipType relationship_type
        +datetime valid_from
        +datetime valid_until
    }

    Asset "1" *-- "0..*" AssetIdentifier : contains
    Asset "1" *-- "0..1" AssetSpecification : describes
    AssetRelationship "*" --> "1" Asset : source
    AssetRelationship "*" --> "1" Asset : target
```

### Responsibilities

**Asset**

Maintains stable asset identity and lifecycle.

**AssetIdentifier**

Represents a namespaced external identifier.

Its equality should be based on its identifying value fields, not an independently generated UUID.

**AssetSpecification**

Defines type-specific attributes through composition.

Potential implementations include:

- NetworkEndpointSpecification.
- CertificateSpecification.
- SoftwareComponentSpecification.
- CryptographicKeySpecification.
- CryptographicModuleSpecification.
- RandomnessComponentSpecification.

**AssetRelationship**

Maintains an independently identifiable relationship between two assets.

## 5. Evidence and Collection Domain

```mermaid
classDiagram
    class EvidenceRecord {
        +UUID evidence_id
        +UUID subject_asset_id
        +EvidenceType evidence_type
        +str property
        +EvidenceValue value
        +EvidenceLifecycleStatus status
        +EvidenceProvenance provenance
        +datetime observed_at
    }

    class EvidenceValue {
        <<Protocol>>
    }

    class EvidenceProvenance {
        +SourceType source_type
        +str source_identifier
        +UUID collection_operation_id
        +str collection_method
        +datetime timestamp
    }

    class CollectionExecution {
        +UUID execution_id
        +str collector_id
        +str collector_version
        +UUID runtime_id
        +datetime started_at
        +datetime completed_at
        +CollectionStatus status
    }

    class CollectionOperation {
        +UUID operation_id
        +str operation_type
        +str target_reference
        +datetime started_at
        +datetime completed_at
        +CollectionStatus status
    }

    class TLSHandshakeObservation {
        +UUID connection_id
        +str target
        +str protocol_version
        +str cipher_suite
        +str negotiated_group
        +str peer_certificate_reference
        +datetime timestamp
    }

    class TLSCapabilityProbeResult {
        +UUID probe_id
        +str requested_protocol
        +str requested_group
        +str client_configuration
        +ProbeOutcome outcome
        +str diagnostic
    }

    EvidenceRecord *-- EvidenceValue : contains
    EvidenceRecord *-- EvidenceProvenance : contains

    CollectionExecution "1" *-- "0..*" CollectionOperation : contains
    CollectionOperation "0..1" --> "0..*" EvidenceRecord : produces

    CollectionOperation *-- TLSHandshakeObservation : may contain
    CollectionOperation *-- TLSCapabilityProbeResult : may contain
```

### Responsibilities

**EvidenceRecord**

Represents a finalized observation, declaration, demonstrated capability or derived result.

It is immutable.

**EvidenceValue**

Represents a typed payload.

Examples include TLS observations, certificate metadata and software component information.

It should not be an unrestricted dictionary.

**EvidenceProvenance**

Preserves the origin of evidence.

It distinguishes collected, declared, imported and derived information.

**CollectionExecution**

Coordinates an individual collector execution.

**CollectionOperation**

Represents a distinct activity within an execution.

**TLSHandshakeObservation**

Describes one actual TLS handshake.

**TLSCapabilityProbeResult**

Describes one controlled capability probe.

Negotiated handshake evidence and capability-probe evidence must remain distinct.

## 6. Runtime Domain

```mermaid
classDiagram
    class RuntimeProfile {
        +UUID runtime_id
        +str operating_system
        +str architecture
        +str python_implementation
        +str python_version
        +str ssl_backend
        +str openssl_version
        +datetime captured_at
    }

    class RuntimeCapabilities {
        +bool negotiated_group_api
        +bool configurable_groups_api
        +tuple available_tls_versions
        +tuple locally_available_groups
        +tuple available_collection_methods
    }

    RuntimeProfile *-- RuntimeCapabilities : describes
    CollectionExecution "*" --> "1" RuntimeProfile : uses
```

### Responsibilities

**RuntimeProfile**

Identifies the environment performing collection.

**RuntimeCapabilities**

Describes locally available collection and cryptographic capabilities.

A runtime capability must never be interpreted as proof of remote endpoint support.

## 7. Standards Domain

```mermaid
classDiagram
    class StandardsReference {
        +UUID reference_id
        +str publisher
        +str document_identifier
        +str title
    }

    class StandardsEdition {
        +UUID edition_id
        +str revision
        +date publication_date
        +date effective_date
        +PublicationStatus status
        +str official_url
    }

    class StandardsProvision {
        +str provision_id
        +str section
        +str title
        +ProvisionType provision_type
        +str requirement_summary
        +str applicability
    }

    StandardsReference "1" *-- "1..*" StandardsEdition : identifies
    StandardsEdition "1" *-- "0..*" StandardsProvision : contains
```

### Responsibilities

**StandardsReference**

Maintains the stable publication identity.

**StandardsEdition**

Represents a specific publication revision.

**StandardsProvision**

Represents a specific provision within an edition.

A standards provision is an immutable value object belonging to an edition.

## 8. Assessment Domain

```mermaid
classDiagram
    class PolicyIdentity {
        +str policy_id
        +str policy_name
        +datetime created_at
    }

    class PolicyVersion {
        +UUID policy_version_id
        +str version
        +str objective
        +tuple scope
        +tuple exclusions
        +datetime effective_from
        +PolicyStatus status
    }

    class PolicyRuleIdentity {
        +str rule_id
        +str name
    }

    class PolicyRuleVersion {
        +UUID rule_version_id
        +str version
        +tuple required_evidence
        +str rationale
    }

    class AssessmentContext {
        +tuple asset_references
        +tuple evidence_references
        +tuple selected_policy_versions
        +str standards_profile
        +datetime assessment_timestamp
    }

    class AssessmentRun {
        +UUID assessment_run_id
        +datetime created_at
        +str methodology_version
        +tuple policy_version_snapshots
        +tuple standards_edition_references
        +tuple evidence_references
    }

    class PolicyResult {
        +UUID policy_result_id
        +UUID policy_version_id
        +PolicyExecutionStatus execution_status
        +tuple limitations
        +tuple diagnostics
    }

    class AssessmentFinding {
        +UUID finding_id
        +AssessmentClassification classification
        +str rationale
        +tuple evidence_references
        +tuple standards_provision_references
        +tuple affected_asset_references
    }

    PolicyIdentity "1" *-- "0..*" PolicyVersion : versions
    PolicyIdentity "1" --> "0..*" PolicyRuleIdentity : defines

    PolicyVersion "1" *-- "1..*" PolicyRuleVersion : contains
    PolicyRuleIdentity "1" --> "0..*" PolicyRuleVersion : versions

    PolicyRuleVersion "*" --> "1..*" StandardsProvision : references

    AssessmentRun *-- AssessmentContext : captures
    AssessmentRun "1" *-- "1..*" PolicyResult : contains
    PolicyVersion "1" --> "0..*" PolicyResult : selected
    PolicyResult "1" *-- "0..*" AssessmentFinding : produces

    AssessmentFinding "*" --> "1" PolicyRuleVersion : evaluated_by
    AssessmentFinding "*" --> "0..*" EvidenceRecord : supported_by
    AssessmentFinding "*" --> "0..*" Asset : concerns
```

### Responsibilities

**PolicyIdentity**

Maintains a stable assessment policy identity.

**PolicyVersion**

Defines one immutable version of the policy specification.

**PolicyRuleIdentity**

Maintains the stable identity of an individual rule.

**PolicyRuleVersion**

Defines the specific requirements, rationale and references for one rule version.

Each rule version belongs to exactly one policy version.

**AssessmentContext**

Provides canonical assets, evidence and assessment configuration.

It must not depend on TLSScanResult or any other collector-specific structure.

**AssessmentRun**

Represents one assessment execution and preserves historical methodology.

**PolicyResult**

Records the execution outcome of one policy version.

**AssessmentFinding**

Records one assessment conclusion with explicit references to its originating rule and supporting evidence.

## 9. Risk and Modernization Domain

```mermaid
classDiagram
    class RiskAssessment {
        +UUID risk_id
        +str exposure_rationale
        +str impact_basis
        +str likelihood_basis
        +str priority
    }

    class ModernizationPlan {
        +UUID plan_id
        +str objective
        +ModernizationStatus status
        +datetime created_at
    }

    class ModernizationTask {
        +UUID task_id
        +UUID plan_id
        +UUID asset_id
        +str proposed_replacement
        +str validation_requirements
        +TaskStatus status
    }

    RiskAssessment "*" --> "0..*" AssessmentFinding : evaluates
    RiskAssessment "*" --> "0..*" Asset : assesses
    ModernizationPlan "1" *-- "0..*" ModernizationTask : contains
    ModernizationTask "*" --> "1" Asset : addresses
    ModernizationTask "*" --> "0..*" AssessmentFinding : responds_to
```

### Responsibilities

**RiskAssessment**

Evaluates technical findings against organizational context.

**ModernizationPlan**

Coordinates cryptographic modernization and migration activities.

**ModernizationTask**

Represents an actionable change affecting an asset.

Risk findings and modernization activities remain separate from technical assessment execution.

## 10. Interface Contracts

The following interfaces should use Python structural typing through `Protocol`.

### Collector

Responsible for collecting evidence.

Conceptual operation:

`collect(request) -> CollectionExecution`

### AssessmentPolicy

Responsible for evaluating an AssessmentContext.

Conceptual operation:

`assess(context) -> PolicyResult`

### AssetRepository

Responsible for retrieving and persisting asset entities.

### EvidenceRepository

Responsible for retrieving and persisting evidence records.

### StandardsRepository

Responsible for retrieving standards references, editions and provisions.

### PolicyRegistry

Responsible for retrieving available policy versions.

### BOMImporter

Responsible for importing external inventory documents.

### BOMExporter

Responsible for exporting standardized inventory documents.

These interfaces should not introduce dependencies on concrete persistence or external library implementations.

## 11. Type and Immutability Strategy

The implementation will use:

- `@dataclass` for domain entities.
- `@dataclass(frozen=True)` for immutable value objects and finalized records.
- `Enum` for controlled domain values.
- `Protocol` for service and collection interfaces.
- Pydantic for external input validation.
- Dedicated serializers for persistence and interoperability.

Nested mutable collections must not be allowed to undermine historical immutability.

Entity equality should be based on stable identity rather than all object fields.

## 12. Design Constraints

1. Asset identity must remain independent of external identifiers.
2. Inventory membership must not duplicate asset identity.
3. Evidence must preserve provenance.
4. Collection executions must reference their runtime.
5. A TLS handshake must describe one connection.
6. Capability probes must retain client configuration and outcome.
7. Assessment policies must consume canonical evidence.
8. Every finding must identify its rule version.
9. Every rule version must belong to one policy version.
10. Standards provisions must belong to a specific edition.
11. Historical assessment results must preserve their original references.
12. CycloneDX objects must not become internal domain models.

## 13. Implementation Readiness

The domain class design is considered ready for implementation when:

- Entity responsibilities are unambiguous.
- Value-object composition is established.
- Aggregate ownership is documented.
- Domain interfaces are defined.
- Immutability requirements are testable.
- Serialization boundaries are established.
- Existing application functionality can be migrated incrementally.

**Guiding principle:** Domain classes represent the framework's concepts and responsibilities. They should not be shaped around the current TLS scanner, JSON format or CycloneDX schema.
