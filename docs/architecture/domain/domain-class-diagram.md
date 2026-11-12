# Domain Class Diagram

**Project:** Cryptographic Inventory, Security Assurance and Modernization Framework

**Version:** 0.1.0

**Status:** Proposed

## 1. Purpose

This document provides a visual representation of the framework's proposed Python domain classes, their composition and references.

It complements `domain-class-design.md` and `entity-relationship-diagram.md`.

The diagrams represent logical class relationships rather than prescribing database structures.

## 2. Organization and Inventory

```mermaid
classDiagram
    class Organization {
        +UUID organization_id
        +str name
        +datetime created_at
    }

    class Inventory {
        +UUID inventory_id
        +UUID organization_id
        +str name
        +InventoryStatus status
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

`InventoryMembership` connects an existing asset to an inventory without duplicating its identity.

## 3. Asset Domain

```mermaid
classDiagram
    class Asset {
        +UUID asset_id
        +AssetType asset_type
        +str name
        +str description
        +tuple identifiers
        +AssetSpecification specification
        +AssetLifecycle lifecycle
        +lifecycle_status
        +created_at
        +updated_at
    }

    class AssetIdentifier {
        +str namespace
        +str value
        +str issuer
        +datetime valid_from
        +datetime valid_until
    }

    class AssetSpecification {
        <<TypeAlias>>
    }

    class CertificateSpecification {
        +str serial_number
        +str subject
        +str issuer
        +CertificateValidity validity
        +str signature_algorithm
        +PublicKeyInfo public_key
    }

    class CertificateValidity {
        +datetime not_before
        +datetime not_after
    }

    class PublicKeyInfo {
        +str algorithm
        +int key_size_bits
        +str curve
    }

    class CryptographicKeyReferenceSpecification {
        +str algorithm
        +int key_size_bits
        +str curve
        +tuple key_usage
    }

    class AssetLifecycle {
        +AssetLifecycleStatus status
        +datetime created_at
        +datetime updated_at
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
    Asset "1" *-- "1" AssetLifecycle : maintains

    CertificateSpecification *-- CertificateValidity
    CertificateSpecification *-- PublicKeyInfo

    AssetRelationship "*" --> "1" Asset : source
    AssetRelationship "*" --> "1" Asset : target
```

`AssetSpecification` is a type alias for the currently supported typed specifications.

An Asset may have no specification when its technical characteristics are not yet established.

`AssetIdentifier` values are composed by Asset and may retain optional validity periods.

`AssetLifecycle` represents the current lifecycle state and timestamps.

`AssetRelationship` references independently identifiable assets and does not own them.

## 4. Evidence and Collection

```mermaid
classDiagram
    class EvidenceRecord {
        +UUID evidence_id
        +SubjectReference subject
        +EvidenceType evidence_type
        +str property
        +EvidenceValue value
        +EvidenceLifecycleStatus lifecycle_status
        +datetime observed_at
    }

    class SubjectReference {
        +SubjectType subject_type
        +UUID subject_id
    }

    class EvidenceValue {
        <<ValueObject>>
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
        +CollectionStatus status
    }

    class CollectionOperation {
        +UUID operation_id
        +str operation_type
        +str target_reference
        +CollectionStatus status
    }

    class TLSHandshakeObservation {
        +UUID connection_id
        +str protocol_version
        +str cipher_suite
        +str negotiated_group
        +str peer_certificate_reference
    }

    class TLSCapabilityProbeResult {
        +UUID probe_id
        +str requested_protocol
        +str requested_group
        +ProbeOutcome outcome
    }

    EvidenceRecord *-- SubjectReference : identifies
    EvidenceRecord *-- EvidenceValue : contains
    EvidenceRecord *-- EvidenceProvenance : contains

    CollectionExecution "1" *-- "0..*" CollectionOperation : contains
    CollectionOperation "1" --> "0..*" EvidenceRecord : produces

    CollectionOperation *-- TLSHandshakeObservation : records
    CollectionOperation *-- TLSCapabilityProbeResult : records
```

Evidence records remain independent of collection execution. Provenance connects collected, declared, imported and derived evidence to their origins.

TLS handshake observations and capability probes represent distinct operations and must not be combined into one observation.

## 5. Runtime Domain

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

Runtime profiles describe the collector environment, not the remote endpoint.

## 6. Standards Domain

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
        +str section
        +str title
        +ProvisionType provision_type
        +str requirement_summary
    }

    StandardsReference "1" *-- "1..*" StandardsEdition : identifies
    StandardsEdition "1" *-- "0..*" StandardsProvision : contains
```

Standards provisions are immutable value objects belonging to a specific edition.

## 7. Assessment Domain

```mermaid
classDiagram
    class PolicyIdentity {
        +str policy_id
        +str policy_name
    }

    class PolicyVersion {
        +UUID policy_version_id
        +str version
        +str objective
        +tuple scope
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
        +str methodology_version
        +datetime created_at
    }

    class PolicyResult {
        +UUID policy_result_id
        +UUID policy_version_id
        +PolicyExecutionStatus execution_status
    }

    class AssessmentFinding {
        +UUID finding_id
        +AssessmentClassification classification
        +str rationale
        +tuple evidence_references
        +tuple affected_asset_references
    }

    PolicyIdentity "1" --> "0..*" PolicyVersion : versions
    PolicyIdentity "1" --> "0..*" PolicyRuleIdentity : defines

    PolicyVersion "1" *-- "1..*" PolicyRuleVersion : contains
    PolicyRuleIdentity "1" --> "0..*" PolicyRuleVersion : versions

    PolicyRuleVersion "*" --> "0..*" StandardsProvision : references

    AssessmentRun *-- AssessmentContext : captures
    AssessmentRun "1" *-- "0..*" PolicyResult : contains
    PolicyResult "*" --> "1" PolicyVersion : executes
    PolicyResult "1" *-- "0..*" AssessmentFinding : produces

    AssessmentFinding "*" --> "1" PolicyRuleVersion : identifies
    AssessmentFinding "*" --> "0..*" EvidenceRecord : references
    AssessmentFinding "*" --> "0..*" Asset : concerns
```

Every rule version belongs to one policy version. Findings identify their exact originating rule version.

A policy rule may have no external standards provision when it represents a documented organizational or project-specific requirement.

## 8. Risk and Modernization

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
    }

    class ModernizationTask {
        +UUID task_id
        +UUID asset_id
        +str proposed_replacement
        +TaskStatus status
    }

    RiskAssessment "*" --> "0..*" AssessmentFinding : evaluates
    RiskAssessment "*" --> "0..*" Asset : assesses

    ModernizationPlan "1" *-- "0..*" ModernizationTask : contains
    ModernizationTask "*" --> "1" Asset : addresses
    ModernizationTask "*" --> "0..*" AssessmentFinding : responds_to
```

Risk assessments consume technical findings and organizational context. Modernization plans coordinate changes without modifying historical assessment results.

## 9. Interface Contracts

The architecture uses Python structural typing through `Protocol` for independently implemented components.

| Protocol | Responsibility |
|---|---|
| `Collector` | Produces collection results and evidence. |
| `AssetRepository` | Manages asset persistence. |
| `EvidenceRepository` | Retrieves and persists evidence. |
| `InventoryRepository` | Manages inventory records. |
| `AssessmentPolicy` | Evaluates an assessment context. |
| `PolicyRegistry` | Resolves policy versions. |
| `StandardsRepository` | Retrieves standards editions and provisions. |
| `BOMImporter` | Imports external inventory documents. |
| `BOMExporter` | Exports standardized inventory documents. |

Interfaces belong to the application boundary requiring the capability. Implementations belong to their respective adapters or infrastructure packages.

## 10. Implementation Constraints

- Entities use stable internal identities.
- Value objects are immutable.
- Aggregate references use identifiers.
- Historical evidence and findings remain immutable.
- Domain objects do not depend on external serialization formats.
- Collectors produce canonical evidence.
- Assessment policies do not depend on collector implementations.

**Guiding principle:** Class composition represents domain responsibilities; interfaces enable independent implementations; immutable records preserve historical meaning.
