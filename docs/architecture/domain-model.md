# Domain Model Specification

**Project:** Cryptographic Inventory, Security Assurance and Modernization Framework
**Version:** 0.1.0
**Status:** Proposed

## 1. Purpose

This document defines the foundational domain entities, their responsibilities, attributes and relationships.

The domain model provides the common conceptual foundation for cryptographic discovery, evidence collection, inventory management, standards-based assessment and cryptographic modernization.

It is independent of specific collection technologies, cryptographic libraries, storage implementations and external inventory formats.

## 2. Architectural Principles

The domain model follows these principles:

1. Every asset has a stable internal identity.
2. External identifiers are maintained separately from internal identifiers.
3. Evidence is associated with the asset it describes.
4. Collection executions preserve evidence provenance.
5. Runtime profiles describe the environment performing collection.
6. Assessment policies consume canonical evidence rather than collector-specific objects.
7. Standards references are independently versioned.
8. Historical evidence and assessment results remain reproducible.
9. Private keys and other secret material are not stored in inventory evidence by default.
10. Domain models remain independent of CycloneDX and persistence technologies.

## 3. Foundational Domain Areas

The domain consists of seven primary areas:

| Domain | Responsibility |
|---|---|
| Assets | Represents identifiable organizational and cryptographic assets. |
| Relationships | Represents dependencies and associations between assets. |
| Evidence | Represents collected, declared and derived information. |
| Collection | Records discovery and evidence collection activities. |
| Runtime | Describes collection environments and capabilities. |
| Standards | Represents authoritative publications and provisions. |
| Assessment | Evaluates evidence against versioned policies and rules. |

Risk assessment and cryptographic modernization build upon these foundational domains.

# 4. Asset Domain

## 4.1 CryptographicAsset

Represents an identifiable system, component, service or cryptographic object that provides, uses, stores or depends on cryptographic functionality.

### Attributes

| Attribute | Type | Required | Description |
|---|---|---|---|
| asset_id | UUID | Yes | Stable internal identifier. |
| asset_type | AssetType | Yes | Classification of the asset. |
| name | String | Yes | Human-readable name. |
| description | String | No | Additional asset information. |
| identifiers | List[AssetIdentifier] | No | External identifiers. |
| owner_reference | Optional UUID | No | Organizational owner. |
| environment | String | No | Production, development, testing, etc. |
| lifecycle_status | AssetLifecycleStatus | Yes | Current lifecycle state. |
| created_at | Timestamp | Yes | Initial registration time. |
| updated_at | Timestamp | Yes | Latest inventory update. |
| metadata | Structured data | No | Type-specific metadata. |

### Initial asset classifications

- Computing assets.
- Application assets.
- Network services.
- Certificate assets.
- Cryptographic key references.
- Software components.
- Cryptographic modules.
- Randomness components.
- Cryptographic services.

These classifications will be refined through the cryptographic asset taxonomy research.

### Identity principle

The internal UUID represents the framework's identity for an asset.

External identifiers, such as hostnames, IP addresses, certificate fingerprints and package identifiers, must not replace the internal identity.

An asset may have several external identifiers, and those identifiers may change during its lifecycle.

The framework must avoid incorrectly creating duplicate assets when an identifier changes.

## 4.2 AssetIdentifier

Represents an identifier associated with an asset.

| Attribute | Type | Description |
|---|---|---|
| identifier_id | UUID | Internal identifier. |
| namespace | String | Identifier namespace or scheme. |
| value | String | Identifier value. |
| issuer | Optional String | Organization or system issuing it. |
| valid_from | Optional Timestamp | Beginning of validity. |
| valid_until | Optional Timestamp | End of validity. |

Examples include DNS names, IP addresses, certificate fingerprints and software package identifiers.

## 4.3 AssetRelationship

Represents a directed relationship between two assets.

| Attribute | Type | Description |
|---|---|---|
| relationship_id | UUID | Stable relationship identifier. |
| source_asset_id | UUID | Originating asset. |
| target_asset_id | UUID | Related asset. |
| relationship_type | RelationshipType | Nature of the relationship. |
| valid_from | Optional Timestamp | Beginning of relationship. |
| valid_until | Optional Timestamp | End of relationship. |
| evidence_references | List[UUID] | Supporting evidence. |
| metadata | Structured data | Additional relationship information. |

Initial relationship types:

- runs
- hosts
- exposes
- presents
- uses
- implements
- depends_on
- managed_by
- protected_by

Relationships must preserve their historical validity where possible.

# 5. Evidence Domain

## 5.1 EvidenceRecord

Represents an individual piece of information associated with an asset.

Evidence is the primary input to the assessment engine.

| Attribute | Type | Required | Description |
|---|---|---|---|
| evidence_id | UUID | Yes | Unique evidence identifier. |
| subject_asset_id | Optional UUID | No | Asset described by the evidence. |
| evidence_type | EvidenceType | Yes | Nature of the evidence. |
| property | String | Yes | Property being described. |
| value | Structured data | Conditional | Collected or derived value. |
| source | String | Yes | Source of the information. |
| collection_execution_id | Optional UUID | No | Associated collection execution. |
| observed_at | Timestamp | Yes | Time of observation or declaration. |
| status | EvidenceStatus | Yes | Evidence collection outcome. |
| runtime_reference | Optional UUID | No | Runtime used during collection. |
| limitations | List[String] | No | Known limitations. |
| metadata | Structured data | No | Additional information. |

### Evidence categories

| Category | Description |
|---|---|
| observed | Directly observed system behaviour or configuration. |
| capability | Demonstrated system capability. |
| declared | Information supplied by an organization or vendor. |
| derived | Information produced through documented analysis. |

Runtime information is represented through a separate RuntimeProfile.

### Evidence statuses

- obtained
- unavailable
- inconclusive
- not_tested
- unsupported
- failed

Evidence category and collection status are independent properties.

For example, a capability probe can have category `capability` and status `inconclusive`.

An unsuccessful probe must not automatically establish that the remote endpoint lacks the tested capability.

### Evidence immutability

Finalized evidence records must be immutable.

A subsequent observation creates a new record rather than overwriting historical evidence.

This supports reproducibility, auditing and configuration-change detection.

## 5.2 Evidence provenance

Evidence must identify how it was obtained.

Its provenance includes, where applicable:

- Collection execution.
- Collection method.
- Source component.
- Runtime profile.
- Collection timestamp.
- Target configuration.
- Probe configuration.
- Diagnostic information.

Derived evidence must identify its originating evidence and transformation logic.

# 6. Collection Domain

## 6.1 CollectionExecution

Represents one execution of a collection operation.

| Attribute | Type | Description |
|---|---|---|
| execution_id | UUID | Unique execution identifier. |
| collector_id | String | Collector identity. |
| collector_version | String | Collector implementation version. |
| started_at | Timestamp | Execution start. |
| completed_at | Optional Timestamp | Execution completion. |
| status | CollectionStatus | Execution outcome. |
| runtime_id | UUID | Runtime used. |
| diagnostics | List | Collection diagnostics. |
| metadata | Structured data | Execution context. |

A collection execution may produce multiple evidence records.

Individual connections and probes must retain their own identifiers within the execution.

## 6.2 TLSHandshakeObservation

Represents one actual TLS handshake.

It contains:

- connection_id
- target_reference
- connection_timestamp
- negotiated_tls_version
- negotiated_cipher_suite
- negotiated_key_establishment_group
- peer_certificate_reference
- certificate_verification_result
- runtime_reference

All negotiated properties must refer to the same connection.

This prevents observations from separate handshakes being presented as one negotiated configuration.

## 6.3 TLSCapabilityProbe

Represents an individual controlled TLS capability test.

It contains:

- probe_id
- target_reference
- probe_type
- client_configuration
- requested_protocol
- requested_group
- outcome
- diagnostic_information
- runtime_reference
- timestamp

Probe outcomes must distinguish successful negotiation, explicit rejection, inconclusive failure and inability to perform the test.

Capability results must retain the limitations of the probing client.

# 7. Runtime Domain

## 7.1 RuntimeProfile

Represents the environment performing collection.

| Attribute | Type | Description |
|---|---|---|
| runtime_id | UUID | Unique runtime identifier. |
| operating_system | String | Operating system. |
| architecture | String | CPU architecture. |
| python_implementation | String | Python implementation. |
| python_version | String | Python version. |
| ssl_backend | String | SSL backend. |
| openssl_version | Optional String | OpenSSL version. |
| library_versions | Structured data | Relevant cryptographic libraries. |
| capabilities_reference | UUID | Associated capability profile. |
| captured_at | Timestamp | Runtime discovery time. |

## 7.2 RuntimeCapabilities

Represents capabilities discovered in the collection runtime.

It should describe:

- Available SSL APIs.
- Available TLS protocol versions.
- Available cryptographic groups.
- Configurable key-establishment groups.
- Certificate validation capabilities.
- Relevant cryptographic algorithms.
- Supported collection methods.

Local cryptographic capabilities must never be interpreted as remote endpoint capabilities.

Scanner runtime and target runtime are separate concepts.

# 8. Standards Domain

## 8.1 StandardsReference

Represents an authoritative standards publication.

| Attribute | Type | Description |
|---|---|---|
| reference_id | Stable identifier | Internal reference identifier. |
| publisher | String | Standards publisher. |
| document_identifier | String | RFC, FIPS, NIST SP, etc. |
| title | String | Publication title. |
| revision | Optional String | Publication revision. |
| publication_date | Optional Date | Publication date. |
| effective_date | Optional Date | Effective date. |
| publication_status | PublicationStatus | Current publication state. |
| official_url | URL | Official publication location. |
| supersedes | List[ReferenceID] | Superseded publications. |

## 8.2 StandardsProvision

Represents an individual provision within a publication.

Attributes:

- provision_id
- reference_id
- section
- title
- provision_type
- requirement_summary
- applicability
- metadata

A provision may support multiple assessment rules.

A reference may contain multiple provisions.

Standards updates must preserve historical versions and relationships.

# 9. Assessment Domain

## 9.1 AssessmentPolicy

Represents an independent security assessment responsibility.

Attributes:

- policy_id
- policy_name
- policy_version
- objective
- scope
- exclusions
- effective_from
- status

Policy identifiers remain stable across versions.

## 9.2 PolicyRule

Represents an individual assessment requirement.

Attributes:

- rule_id
- policy_id
- rule_version
- name
- description
- required_evidence
- evaluation_logic
- rationale
- standards_provision_references
- effective_from
- status

Rules must identify their evidence requirements and supporting standards provisions.

## 9.3 AssessmentContext

Supplies the information required by assessment policies.

It includes:

- assessment scope
- asset references
- evidence references
- policy selection
- standards profile
- organizational context
- assessment timestamp

It must not depend directly on collector-specific result structures such as TLSScanResult.

## 9.4 AssessmentRun

Represents one complete assessment execution.

Attributes:

- assessment_run_id
- created_at
- assessment_scope
- methodology_version
- policy_version_snapshots
- standards_version_snapshots
- evidence_references
- runtime_references
- execution_results

Historical assessment runs must preserve the policy, rule and standards versions used.

## 9.5 PolicyResult

Represents the execution result of an individual policy.

Attributes:

- policy_id
- policy_version
- execution_status
- findings
- limitations
- diagnostics

Policy execution status is independent of finding classification.

A policy may complete successfully while producing findings classified as unknown.

## 9.6 AssessmentFinding

Represents an individual assessment conclusion.

Attributes:

- finding_id
- asset_references
- policy_id
- policy_version
- rule_id
- rule_version
- classification
- rationale
- evidence_references
- standards_provision_references
- limitations

Every finding must be traceable to its originating assessment rule and supporting evidence.

# 10. Risk Domain

Risk assessment consumes technical assessment results together with organizational context.

The initial RiskAssessment model should support:

- risk_id
- affected_asset_references
- related_finding_references
- business_context
- exposure_rationale
- likelihood_basis
- impact_basis
- migration_priority
- recommendations

Numerical risk scoring will require a separately documented and validated methodology.

# 11. Domain Relationships

The principal relationships are:

| Relationship | Cardinality | Description |
|---|---|---|
| Asset to Identifier | One-to-many | An asset may have several identifiers. |
| Asset to Relationship | One-to-many | An asset may participate in multiple relationships. |
| Asset to Evidence | One-to-many | An asset may have many historical evidence records. |
| CollectionExecution to Evidence | One-to-many | An execution may produce multiple evidence records. |
| RuntimeProfile to CollectionExecution | One-to-many | A runtime may perform multiple executions. |
| StandardsReference to StandardsProvision | One-to-many | A publication may contain multiple provisions. |
| AssessmentPolicy to PolicyRule | One-to-many | A policy defines multiple rules. |
| AssessmentRun to PolicyResult | One-to-many | An assessment run executes multiple policies. |
| PolicyResult to AssessmentFinding | One-to-many | A policy execution produces multiple findings. |
| PolicyRule to StandardsProvision | Many-to-many | Rules may reference multiple provisions. |
| AssessmentFinding to Evidence | Many-to-many | Findings may use multiple evidence records. |
| RiskAssessment to AssessmentFinding | Many-to-many | Risk assessments may evaluate multiple findings. |

# 12. Domain Invariants

The implementation must enforce these invariants:

| ID | Invariant |
|---|---|
| DM-001 | Every asset has a stable internal UUID. |
| DM-002 | External asset identifiers are separate from internal identity. |
| DM-003 | Evidence identifies the asset it describes, where applicable. |
| DM-004 | Evidence retains its provenance. |
| DM-005 | Negotiated handshake properties belong to one connection observation. |
| DM-006 | Capability probes preserve client configuration and outcomes. |
| DM-007 | Scanner runtime and target runtime remain separate. |
| DM-008 | Finalized historical evidence is immutable. |
| DM-009 | Every finding references its originating policy rule. |
| DM-010 | Assessment rules reference applicable standards provisions. |
| DM-011 | Historical assessments preserve their methodology and policy versions. |
| DM-012 | Missing evidence does not automatically imply security or insecurity. |
| DM-013 | Secret cryptographic material is not collected by default. |

# 13. Serialization and External Interoperability

Domain objects must remain independent of JSON, database and CycloneDX-specific representations.

Dedicated serialization and mapping components will handle external formats.

The framework will maintain:

1. Canonical domain models.
2. Versioned native evidence contracts.
3. Assessment result contracts.
4. CycloneDX inventory mappings.

CycloneDX is an interoperability format, not the internal domain model.

# 14. Implementation Strategy

The domain model will be implemented incrementally.

The initial implementation priorities are:

1. Asset and identifier models.
2. Asset relationship models.
3. Evidence and provenance models.
4. Collection execution models.
5. Runtime profiles and capabilities.
6. Standards references and provisions.
7. Assessment context and execution models.
8. Risk models.

Existing TLS and assessment contracts will be migrated incrementally, preserving backward compatibility where practical.

No existing functionality should be removed merely to accommodate the new architecture.

---

**Guiding principle:** Assets represent what exists, evidence represents what is known, collection represents how knowledge was obtained, standards represent authoritative requirements, and assessment represents the interpretation of evidence against those requirements.
