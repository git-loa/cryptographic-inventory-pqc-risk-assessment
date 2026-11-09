# Domain Entity Relationship Diagram

**Project:** Cryptographic Inventory, Security Assurance and Modernization Framework

**Version:** 0.1.0

**Status:** Proposed

## 1. Purpose

This document defines the entity relationships and cardinalities of the framework.

It provides a consolidated view of organizational inventory, cryptographic assets, evidence collection, runtime provenance, standards management, assessment execution and risk analysis.

The diagram represents logical domain relationships. It does not prescribe a particular relational database or persistence implementation.

## 2. Organizational Inventory Relationships

```mermaid
erDiagram
    ORGANIZATION ||--o{ INVENTORY : maintains
    INVENTORY ||--o{ INVENTORY_MEMBERSHIP : contains
    ASSET ||--o{ INVENTORY_MEMBERSHIP : belongs_through

    ORGANIZATION {
        UUID organization_id PK
        string name
        datetime created_at
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
        datetime created_at
    }
```

An organization maintains inventories.

An asset can participate in multiple inventories through separate membership records.

This avoids duplicating an asset when it belongs to multiple organizational inventory scopes.

## 3. Asset Relationships

```mermaid
erDiagram
    ASSET ||--o{ ASSET_RELATIONSHIP : originates
    ASSET ||--o{ ASSET_RELATIONSHIP : relates_to
    ASSET ||--o{ ASSET_IDENTIFIER : identified_by
    ASSET ||--o| ASSET_SPECIFICATION : described_by

    ASSET {
        UUID asset_id PK
        string asset_type
        string name
        string lifecycle_status
    }

    ASSET_IDENTIFIER {
        string namespace
        string value
        string issuer
    }

    ASSET_SPECIFICATION {
        string specification_type
        string specification_data
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

Asset identifiers and specifications are value objects composed into the Asset aggregate.

The diagram represents their conceptual relationships. They do not necessarily require independent domain entity identities.

Asset relationships are independently identifiable because they have their own lifecycle and supporting evidence.

A relationship must identify both its source and target assets.

## 4. Evidence and Collection Relationships

```mermaid
erDiagram
    ASSET ||--o{ EVIDENCE_RECORD : described_by

    COLLECTION_EXECUTION ||--|{ COLLECTION_OPERATION : contains
    COLLECTION_OPERATION ||--o{ EVIDENCE_RECORD : produces

    RUNTIME_PROFILE ||--o{ COLLECTION_EXECUTION : executes

    EVIDENCE_RECORD {
        UUID evidence_id PK
        UUID subject_asset_id FK
        UUID collection_operation_id FK
        UUID runtime_id FK
        string evidence_type
        string property
        string status
        datetime observed_at
    }

    COLLECTION_EXECUTION {
        UUID execution_id PK
        string collector_id
        string collector_version
        UUID runtime_id FK
        datetime started_at
        datetime completed_at
        string execution_status
    }

    COLLECTION_OPERATION {
        UUID operation_id PK
        UUID execution_id FK
        string operation_type
        string operation_status
        string target_reference
    }

    RUNTIME_PROFILE {
        UUID runtime_id PK
        string operating_system
        string architecture
        string python_version
        string ssl_backend
        string openssl_version
        datetime captured_at
    }
```

A collection execution contains one or more collection operations.

Each operation may produce zero or more evidence records.

An execution may therefore complete partially or fail without necessarily producing evidence for every requested operation.

Declared or imported evidence may not have a collection operation. Its provenance must identify the appropriate external source instead.

Runtime profiles represent the collector environment, not the remote target environment.

## 5. Standards Relationships

```mermaid
erDiagram
    STANDARDS_REFERENCE ||--|{ STANDARDS_EDITION : has
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
        UUID provision_id PK
        UUID edition_id FK
        string section
        string title
        string provision_type
        string requirement_summary
    }
```

A standards reference represents a publication identity.

An edition represents a particular publication revision.

A provision belongs to exactly one edition.

Historical editions must remain available for assessment reproducibility.

## 6. Assessment Relationships

```mermaid
erDiagram
    POLICY_IDENTITY ||--o{ POLICY_VERSION : versions
    POLICY_IDENTITY ||--o{ POLICY_RULE_IDENTITY : defines

    POLICY_VERSION ||--|{ POLICY_RULE_VERSION : contains
    POLICY_RULE_IDENTITY ||--o{ POLICY_RULE_VERSION : versions

    POLICY_RULE_VERSION }o--o{ STANDARDS_PROVISION : references

    ASSESSMENT_RUN ||--|{ POLICY_RESULT : executes
    POLICY_VERSION ||--o{ POLICY_RESULT : selected_for

    POLICY_RESULT ||--o{ ASSESSMENT_FINDING : produces

    ASSESSMENT_FINDING }o--o{ EVIDENCE_RECORD : supported_by
    ASSESSMENT_FINDING }o--o{ STANDARDS_PROVISION : justified_by
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

A stable policy identity may have multiple versions.

Each rule identity may also have multiple versions.

A rule version belongs to exactly one policy version.

Policy rules reference exact standards provisions.

Assessment findings reference the specific rule version that produced them.

Findings can reference multiple evidence records and may concern multiple assets.

The policy result records execution status independently of finding classifications.

## 7. Risk and Modernization Relationships

```mermaid
erDiagram
    RISK_ASSESSMENT }o--o{ ASSESSMENT_FINDING : evaluates
    RISK_ASSESSMENT }o--o{ ASSET : evaluates
    MODERNIZATION_PLAN }o--o{ ASSET : addresses
    MODERNIZATION_PLAN }o--o{ ASSESSMENT_FINDING : responds_to

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
```

Risk assessments consume technical findings and organizational context.

Modernization plans coordinate changes to affected assets and respond to identified findings.

Risk evaluation and migration activities remain separate from technical assessment execution.

## 8. Relationship and Ownership Rules

| Relationship | Cardinality | Ownership |
|---|---|---|
| Organization to Inventory | 1:N | Inventory references Organization |
| Inventory to Membership | 1:N | Inventory owns membership records |
| Asset to Membership | 1:N | Membership references Asset |
| Asset to Identifier | 1:N | Asset composes identifiers |
| Asset to Specification | 1:0..1 | Asset composes its specification |
| Asset to Evidence | 1:N | Evidence independently references Asset |
| CollectionExecution to Operation | 1:N | Execution owns operations |
| CollectionOperation to Evidence | 1:N | Operation produces evidence |
| RuntimeProfile to CollectionExecution | 1:N | Execution references RuntimeProfile |
| StandardsReference to Edition | 1:N | Edition references publication identity |
| StandardsEdition to Provision | 1:N | Edition owns provisions |
| PolicyIdentity to PolicyVersion | 1:N | Version references policy identity |
| PolicyVersion to RuleVersion | 1:N | Version owns applicable rule versions |
| RuleIdentity to RuleVersion | 1:N | Version references rule identity |
| PolicyResult to Finding | 1:N | Result owns findings |
| Finding to Evidence | N:M | Finding references evidence |
| Finding to StandardsProvision | N:M | Finding references provisions |
| Finding to Asset | N:M | Finding identifies affected assets |
| RiskAssessment to Finding | N:M | Risk assessment references findings |
| ModernizationPlan to Asset | N:M | Plan references affected assets |

## 9. Important Constraints

The implementation must enforce:

1. Asset identifiers are namespaced.
2. Inventory membership must not duplicate asset identity.
3. Asset relationships cannot reference nonexistent assets.
4. Collection executions must identify their runtime.
5. Failed collection operations must not create invented evidence.
6. Finalized evidence records must be immutable.
7. Historical standards editions must remain identifiable.
8. Every rule version must belong to one policy version.
9. Every finding must reference its originating rule version.
10. Historical assessment runs must preserve their policy and standards references.
11. Risk assessments must reference the technical findings they evaluate.
12. Private keys and secret material must not be stored as ordinary inventory values.

## 10. Design Limitations

This ERD is a logical domain model.

It does not prescribe:

- SQL table names.
- Foreign-key implementation details.
- Database technology.
- JSON serialization.
- ORM relationships.
- CycloneDX component structure.

Those decisions belong to later persistence and interoperability design.

**Guiding principle:** Model the relationships required by the cryptographic domain before selecting the technology used to store them.
