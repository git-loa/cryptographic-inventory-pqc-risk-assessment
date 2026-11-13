# Domain Class Diagram

**Project:** Cryptographic Inventory, Security Assurance and Modernization Framework

**Version:** 0.1.0

**Status:** Proposed

## 1. Purpose

This document illustrates the main domain classes, their attributes and how they connect.

The diagrams represent the logical design, not a database schema. Class responsibilities are described in `domain-class-design.md`.

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
    }

    Organization "1" --> "0..*" Inventory : maintains
    Inventory "1" *-- "0..*" InventoryMembership : contains
    InventoryMembership "*" --> "1" Asset : references
```

An asset may participate in multiple inventories without duplicating its identity.

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

    class NetworkEndpointSpecification {
        +str service_protocol
        +int port
        +str transport_protocol
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

    class SoftwareComponentSpecification {
        +str name
        +str version
        +str vendor
        +str ecosystem
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

    Asset "1" *-- "0..*" AssetIdentifier : contains
    Asset "1" *-- "0..1" AssetSpecification : describes
    Asset "1" *-- "1" AssetLifecycle : maintains

    note for AssetSpecification "Union of the four specification types shown below."

    CertificateSpecification *-- CertificateValidity
    CertificateSpecification *-- PublicKeyInfo
```

An Asset owns its identifiers, optional specification and lifecycle information.

## 4. Asset Relationships

```mermaid
classDiagram
    class AssetRelationship {
        +UUID relationship_id
        +UUID source_asset_id
        +UUID target_asset_id
        +RelationshipType relationship_type
        +datetime valid_from
        +datetime valid_until
        +tuple evidence_references
    }

    class RelationshipType {
        <<enumeration>>
        HOSTS
        RUNS
        EXPOSES
        PRESENTS
        USES
        PROVIDES
        DEPENDS_ON
        MANAGED_BY
        CONTAINS
    }

    class Asset

    AssetRelationship --> RelationshipType : classified by
    AssetRelationship "*" --> "1" Asset : source
    AssetRelationship "*" --> "1" Asset : target
```

Relationships have their own identities and reference assets through UUIDs.

The relationship rules check whether the source and target asset classifications are compatible.

## 5. Evidence and Collection

```mermaid
classDiagram
    class EvidenceRecord {
        +UUID evidence_id
        +SubjectReference subject
        +EvidenceType evidence_type
        +str property
        +EvidenceValue value
        +EvidenceProvenance provenance
        +datetime observed_at
        +EvidenceLifecycleStatus lifecycle_status
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
    }

    class TLSCapabilityProbeResult {
        +UUID probe_id
        +str requested_protocol
        +str requested_group
        +ProbeOutcome outcome
    }

    EvidenceRecord *-- SubjectReference
    EvidenceRecord *-- EvidenceValue
    EvidenceRecord *-- EvidenceProvenance

    CollectionExecution "1" *-- "0..*" CollectionOperation
    CollectionOperation --> EvidenceRecord : produces
    CollectionOperation *-- TLSHandshakeObservation
    CollectionOperation *-- TLSCapabilityProbeResult
```

Collection operations may produce evidence. Evidence can also originate from imports, declarations or analysis without an internal collection operation.

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
    RuntimeProfile "1" --> "0..*" CollectionExecution : supports
```

The runtime describes the environment performing collection, not the remote endpoint.

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
        +str section
        +str title
        +ProvisionType provision_type
        +str requirement_summary
    }

    StandardsReference "1" *-- "0..*" StandardsEdition : identifies
    StandardsEdition "1" *-- "0..*" StandardsProvision : contains
```

Each provision belongs to a particular publication edition.

## 8. Assessment Domain

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

    AssessmentRun *-- AssessmentContext
    AssessmentRun "1" *-- "0..*" PolicyResult : contains
    PolicyResult "*" --> "1" PolicyVersion : executes
    PolicyResult "1" *-- "0..*" AssessmentFinding : produces

    AssessmentFinding "*" --> "1" PolicyRuleVersion : identifies
    AssessmentFinding "*" --> "0..*" EvidenceRecord : references
    AssessmentFinding "*" --> "0..*" Asset : concerns
```

Findings identify their originating rule version and reference the evidence and assets involved.

## 9. Risk and Modernization

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
    ModernizationTask "*" --> "0..*" AssessmentFinding : responds to
```

Risk assessments evaluate findings. Modernization plans organize changes to affected assets.

**Guiding principle:** The diagrams show what the domain classes represent and how they connect. Detailed responsibilities and validation rules are defined in `domain-class-design.md`.
