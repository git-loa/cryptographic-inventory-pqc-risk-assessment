# Domain Entity Relationship Diagram

**Project:** Cryptographic Inventory, Security Assurance and Modernization Framework

**Version:** 0.1.0

**Status:** Proposed

## 1. Purpose

This document illustrates how the framework's main entities are connected.

It shows their ownership, references and cardinalities. The diagrams describe the logical domain model, not a required database structure.

## 2. Organization and Inventory

```mermaid
erDiagram
    ORGANIZATION ||--o{ INVENTORY : maintains
    INVENTORY ||--o{ INVENTORY_MEMBERSHIP : contains
    ASSET ||--o{ INVENTORY_MEMBERSHIP : participates_in

    ORGANIZATION {
        UUID organization_id PK
        string name
    }

    INVENTORY {
        UUID inventory_id PK
        UUID organization_id FK
        string name
        string status
    }

    INVENTORY_MEMBERSHIP {
        UUID membership_id PK
        UUID inventory_id FK
        UUID asset_id FK
    }

    ASSET {
        UUID asset_id PK
        string asset_type
        string name
    }
```

An asset may belong to multiple inventories without creating duplicate asset records.

## 3. Assets and Relationships

```mermaid
erDiagram
    ASSET ||--o{ ASSET_RELATIONSHIP : source
    ASSET ||--o{ ASSET_RELATIONSHIP : target

    ASSET {
        UUID asset_id PK
        string asset_type
        string name
        string lifecycle_status
    }

    ASSET_RELATIONSHIP {
        UUID relationship_id PK
        UUID source_asset_id FK
        UUID target_asset_id FK
        string relationship_type
        datetime valid_from
        datetime valid_until
    }
```

An Asset owns its identifiers, specification and lifecycle information.

An AssetRelationship has its own identity and references two assets by UUID. It may also contain supporting evidence references.

Relationships are directed. The same two assets may have different relationships when they represent different facts.

## 4. Evidence and Collection

```mermaid
erDiagram
    RUNTIME_PROFILE ||--o{ COLLECTION_EXECUTION : supports
    COLLECTION_EXECUTION ||--o{ COLLECTION_OPERATION : contains
    COLLECTION_OPERATION o|--o{ EVIDENCE_RECORD : produces

    RUNTIME_PROFILE {
        UUID runtime_id PK
        string operating_system
        string architecture
        string python_version
        string openssl_version
    }

    COLLECTION_EXECUTION {
        UUID execution_id PK
        UUID runtime_id FK
        string collector_id
        string collector_version
        string status
        datetime started_at
        datetime completed_at
    }

    COLLECTION_OPERATION {
        UUID operation_id PK
        UUID execution_id FK
        string operation_type
        string target_reference
        string status
    }

    EVIDENCE_RECORD {
        UUID evidence_id PK
        string subject_type
        UUID subject_id
        string evidence_type
        string property
        string lifecycle_status
        datetime observed_at
    }
```

An execution may contain multiple operations. An operation may produce zero or more evidence records.

An evidence record may have no internal collection operation when it originates from an external declaration, import or documented analysis.

Its subject reference identifies what the evidence describes. It is not necessarily a direct reference to an Asset.

## 5. Standards

```mermaid
erDiagram
    STANDARDS_REFERENCE ||--o{ STANDARDS_EDITION : identifies
    STANDARDS_EDITION ||--o{ STANDARDS_PROVISION : contains

    STANDARDS_REFERENCE {
        UUID reference_id PK
        string publisher
        string document_identifier
        string title
    }

    STANDARDS_EDITION {
        UUID edition_id PK
        UUID reference_id FK
        string revision
        date publication_date
        date effective_date
        string publication_status
        string official_url
    }

    STANDARDS_PROVISION {
        string section
        string title
        string provision_type
    }
```

A StandardsReference identifies a publication. Each edition represents a particular revision.

`StandardsProvision` is an immutable value object contained within an edition, not an independently identified entity.

## 6. Assessment

```mermaid
erDiagram
    POLICY_IDENTITY ||--o{ POLICY_VERSION : versions
    POLICY_IDENTITY ||--o{ POLICY_RULE_IDENTITY : defines

    POLICY_VERSION ||--|{ POLICY_RULE_VERSION : contains
    POLICY_RULE_IDENTITY ||--o{ POLICY_RULE_VERSION : versions

    ASSESSMENT_RUN ||--o{ POLICY_RESULT : contains
    POLICY_VERSION ||--o{ POLICY_RESULT : evaluates
    POLICY_RESULT ||--o{ ASSESSMENT_FINDING : produces

    POLICY_RULE_VERSION ||--o{ ASSESSMENT_FINDING : originates

    POLICY_RULE_VERSION }o--o{ STANDARDS_PROVISION : references
    ASSESSMENT_FINDING }o--o{ EVIDENCE_RECORD : supported_by
    ASSESSMENT_FINDING }o--o{ ASSET : concerns
```

Each rule version belongs to one policy version.

An AssessmentRun contains its assessment context and policy results. A PolicyResult records the execution status and owns the findings it produces.

Every finding references its originating rule version, supporting evidence and affected assets.

A successfully executed policy may produce findings classified as unknown when the available evidence is insufficient.

## 7. Risk and Modernization

```mermaid
erDiagram
    RISK_ASSESSMENT }o--o{ ASSESSMENT_FINDING : evaluates
    RISK_ASSESSMENT }o--o{ ASSET : assesses

    MODERNIZATION_PLAN ||--o{ MODERNIZATION_TASK : contains
    ASSET ||--o{ MODERNIZATION_TASK : affected_by
    MODERNIZATION_TASK }o--o{ ASSESSMENT_FINDING : addresses
```

Risk assessments evaluate findings and affected assets.

Modernization plans contain tasks that address affected assets and assessment findings.

Historical assessment results remain unchanged by subsequent modernization activities.

## 8. Relationship Summary

| Relationship | Cardinality |
|---|---|
| Organization → Inventory | 1:N |
| Inventory → InventoryMembership | 1:N |
| Asset → InventoryMembership | 1:N |
| Asset → AssetRelationship | 1:N participation |
| RuntimeProfile → CollectionExecution | 1:N |
| CollectionExecution → CollectionOperation | 1:N |
| CollectionOperation → EvidenceRecord | 1:N; operation optional |
| StandardsReference → StandardsEdition | 1:N |
| StandardsEdition → StandardsProvision | 1:N |
| PolicyIdentity → PolicyVersion | 1:N |
| PolicyVersion → PolicyRuleVersion | 1:N |
| AssessmentRun → PolicyResult | 1:N |
| PolicyResult → AssessmentFinding | 1:N |
| AssessmentFinding → EvidenceRecord | N:M |
| AssessmentFinding → Asset | N:M |
| PolicyRuleVersion → StandardsProvision | N:M |
| RiskAssessment → AssessmentFinding | N:M |
| ModernizationPlan → ModernizationTask | 1:N |

## 9. Design Rules

1. Internal asset identities remain stable.
2. Inventory membership does not duplicate assets.
3. Relationships reference assets by UUID.
4. Evidence preserves its subject and origin.
5. Collection outcomes remain separate from evidence values.
6. Historical evidence and assessment results are preserved.
7. Every finding identifies its originating rule version.
8. Standards provisions belong to a specific edition.
9. Missing evidence does not establish security or insecurity.
10. Private keys and secret material are not stored as ordinary inventory data.

**Guiding principle:** Entities maintain their own information, references connect independent entities, and historical records preserve previous decisions and observations.
