# Domain Entity Relationship Diagram

**Project:** Cryptographic Inventory, Security Assurance and Modernization Framework

**Version:** 0.1.0

**Status:** Proposed

## 1. Purpose

This document provides a visual representation of the framework's domain relationships, ownership and cardinalities.

It complements `domain-model.md` and `entity-relationships.md`. It describes logical relationships rather than prescribing a database implementation.

## 2. Organization and Inventory

An organization maintains inventories. Assets participate in inventories through membership records.

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
        datetime valid_from
        datetime valid_until
    }

    ASSET {
        UUID asset_id PK
        string asset_type
        string name
        string lifecycle_status
    }
```

An asset may participate in multiple inventories without duplicating its identity.

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

Each relationship connects two assets and has its own identity and lifecycle.

`AssetIdentifier` and `AssetSpecification` are value objects composed into an asset. They are not independent domain entities.

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
        string ssl_backend
        string openssl_version
    }

    COLLECTION_EXECUTION {
        UUID execution_id PK
        string collector_id
        string collector_version
        UUID runtime_id FK
        datetime started_at
        datetime completed_at
        string status
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
        string subject_reference
        UUID collection_operation_id FK
        string evidence_type
        string property
        string lifecycle_status
        datetime observed_at
    }
```

An execution may contain zero or more operations. An operation may produce zero or more evidence records.

Evidence originating from declarations, imports or derivations may have no internal collection operation.

The `subject_reference` identifies the asset, organization or other subject described. It is a logical reference, not necessarily a direct foreign key to an asset.

Evidence provenance identifies the source and collection history.

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
        UUID provision_id
        UUID edition_id
        string section
        string title
        string provision_type
    }
```

A standards reference identifies a publication, an edition identifies a specific revision, and provisions belong to that edition.

`StandardsProvision` is logically represented here but is implemented as an immutable value object within a standards edition.

## 6. Assessment

```mermaid
erDiagram
    POLICY_IDENTITY ||--o{ POLICY_VERSION : versions
    POLICY_IDENTITY ||--o{ POLICY_RULE_IDENTITY : defines

    POLICY_VERSION ||--|{ POLICY_RULE_VERSION : contains
    POLICY_RULE_IDENTITY ||--o{ POLICY_RULE_VERSION : versions

    POLICY_VERSION ||--o{ POLICY_RESULT : selected_for
    ASSESSMENT_RUN ||--|{ POLICY_RESULT : contains
    POLICY_RESULT ||--o{ ASSESSMENT_FINDING : produces

    POLICY_RULE_VERSION ||--o{ ASSESSMENT_FINDING : originates

    POLICY_RULE_VERSION }o--o{ STANDARDS_PROVISION : references
    ASSESSMENT_FINDING }o--o{ EVIDENCE_RECORD : supported_by
    ASSESSMENT_FINDING }o--o{ ASSET : concerns

    POLICY_IDENTITY {
        string policy_id PK
        string policy_name
    }

    POLICY_VERSION {
        UUID policy_version_id PK
        string policy_id FK
        string version
        string status
    }

    POLICY_RULE_IDENTITY {
        string rule_id PK
        string policy_id FK
        string name
    }

    POLICY_RULE_VERSION {
        UUID rule_version_id PK
        string rule_id FK
        UUID policy_version_id FK
        string version
    }

    ASSESSMENT_RUN {
        UUID assessment_run_id PK
        datetime created_at
        string methodology_version
    }

    POLICY_RESULT {
        UUID policy_result_id PK
        UUID assessment_run_id FK
        UUID policy_version_id FK
        string execution_status
    }

    ASSESSMENT_FINDING {
        UUID finding_id PK
        UUID policy_result_id FK
        UUID rule_version_id FK
        string classification
        string rationale
    }
```

Important constraints:

- Every rule version belongs to exactly one policy version.
- Every finding references its originating rule version.
- The finding's rule version must belong to the policy version executed by its policy result.
- Findings reference evidence and affected assets without owning them.
- Policy execution status is independent of finding classification.
- A rule may have no external standards references when it represents a documented organizational or project-specific requirement.

## 7. Risk and Modernization

```mermaid
erDiagram
    RISK_ASSESSMENT }o--o{ ASSESSMENT_FINDING : evaluates
    RISK_ASSESSMENT }o--o{ ASSET : assesses

    MODERNIZATION_PLAN ||--o{ MODERNIZATION_TASK : contains
    ASSET ||--o{ MODERNIZATION_TASK : affected_by
    MODERNIZATION_TASK }o--o{ ASSESSMENT_FINDING : addresses

    RISK_ASSESSMENT {
        UUID risk_id PK
        string exposure_rationale
        string impact_basis
        string likelihood_basis
        string priority
    }

    MODERNIZATION_PLAN {
        UUID plan_id PK
        string objective
        string status
        datetime created_at
    }

    MODERNIZATION_TASK {
        UUID task_id PK
        UUID plan_id FK
        UUID asset_id FK
        string proposed_replacement
        string status
    }
```

Risk assessments consume technical findings and organizational context.

Modernization plans coordinate changes to affected assets and address identified findings.

Neither modifies historical assessment records.

## 8. Relationship Summary

| Relationship | Cardinality |
|---|---|
| Organization → Inventory | 1:N |
| Inventory → InventoryMembership | 1:N |
| Asset → InventoryMembership | 1:N |
| Asset → AssetRelationship | 1:N participation |
| RuntimeProfile → CollectionExecution | 1:N |
| CollectionExecution → CollectionOperation | 1:N |
| CollectionOperation → EvidenceRecord | 1:N, operation optional |
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

## 9. Design Constraints

1. Internal asset identities must remain stable.
2. Inventory membership must not duplicate assets.
3. Asset relationships must reference existing assets.
4. Evidence must preserve its subject and provenance.
5. Failed collection operations must not create artificial evidence.
6. Runtime capabilities must not be confused with remote capabilities.
7. Historical evidence and assessment results must remain immutable.
8. Findings must reference exact rule versions.
9. Standards provisions must identify their originating editions.
10. Private keys and secret material must not be stored as ordinary inventory data.

**Guiding principle:** The ERD represents domain relationships and ownership, independently of database and serialization technologies.
