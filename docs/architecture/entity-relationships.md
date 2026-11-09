# Entity Relationship and Class Responsibility Specification

**Project:** Cryptographic Inventory, Security Assurance and Modernization Framework
**Version:** 0.1.0
**Status:** Proposed

## 1. Purpose

This document defines the relationships, ownership rules, class responsibilities and object composition of the framework's domain model.

It refines the foundational domain model into an implementation-oriented design.

The objective is to establish clear boundaries between domain entities, value objects, collection activities, evidence, assessment specifications and assessment results.

## 2. Modelling Principles

The design follows these principles:

1. Entities have stable identities and lifecycles.
2. Value objects represent descriptive information without independent identity.
3. Domain objects reference other aggregates through identifiers.
4. Historical evidence and assessment snapshots are immutable.
5. Relationships are explicit rather than hidden in arbitrary dictionaries.
6. Composition is preferred over unnecessary inheritance.
7. Domain models remain independent of external serialization formats.
8. Assessment implementations remain independent of collection implementations.

## 3. Organizational and Inventory Domain

### 3.1 Organization

Represents an organization whose cryptographic infrastructure is inventoried and assessed.

Responsibilities:

- Maintain organizational identity.
- Establish ownership boundaries.
- Associate inventories with organizational units.
- Supply organizational context for risk assessments.

### 3.2 Inventory

Represents a defined collection of organizational assets.

Responsibilities:

- Identify an inventory scope.
- Associate discovered assets with the inventory.
- Maintain inventory metadata.
- Support historical inventory snapshots.
- Provide the scope for discovery and assessment operations.

### Relationships

| Relationship | Cardinality |
|---|---|
| Organization → Inventory | One-to-many |
| Inventory → Asset | One-to-many |
| Inventory → InventorySnapshot | One-to-many |

An asset belongs to an inventory scope in the initial implementation.

Future requirements may justify shared asset membership across multiple inventories.

## 4. Asset Domain

### 4.1 CryptographicAsset

**Type:** Entity

**Identity:** `asset_id`

Responsibilities:

- Maintain stable asset identity.
- Classify the asset.
- Maintain external identifiers.
- Track lifecycle information.
- Associate asset metadata.
- Support asset inventory operations.

The common asset model should not contain every possible field required by specialized asset types.

Type-specific information should be represented through composition.

### 4.2 AssetIdentifier

**Type:** Value object

Responsibilities:

- Represent external identification schemes.
- Preserve identifier namespaces.
- Record issuer and validity information.
- Support identity matching.

An asset may have multiple identifiers.

### 4.3 AssetSpecification

**Type:** Typed value object

Represents type-specific descriptive information.

Examples:

- Certificate specification.
- TLS endpoint specification.
- Software component specification.
- Cryptographic key specification.
- HSM specification.
- Random bit generator specification.

This avoids creating a large inheritance hierarchy.

### 4.4 AssetRelationship

**Type:** Entity

**Identity:** `relationship_id`

Responsibilities:

- Connect two assets.
- Identify relationship types.
- Track relationship validity.
- Reference supporting evidence.
- Preserve historical dependency information.

A relationship is directed from one asset to another.

## 5. Evidence Domain

### 5.1 EvidenceRecord

**Type:** Immutable entity

**Identity:** `evidence_id`

Responsibilities:

- Represent one observation or documented claim.
- Identify the asset described.
- Preserve the evidence value.
- Identify its origin and collection method.
- Record collection status.
- Preserve provenance and limitations.

Evidence must not be overwritten after finalization.

New observations create new evidence records.

### 5.2 EvidenceProvenance

**Type:** Value object

Responsibilities:

- Describe the originating source.
- Identify the collection method.
- Reference the associated collection execution.
- Reference the runtime profile where applicable.
- Record supporting metadata.

Declared and imported evidence may not originate from an application collection execution.

### 5.3 EvidenceValue

**Type:** Typed value object

Responsibilities:

- Represent normalized evidence values.
- Support primitive and structured values.
- Preserve the property's semantic type.
- Avoid dependence on arbitrary unvalidated dictionaries.

Evidence payloads should use property-specific schemas.

## 6. Collection Domain

### 6.1 CollectionExecution

**Type:** Entity

**Identity:** `execution_id`

Responsibilities:

- Identify one collection operation.
- Record collector identity and version.
- Record execution timing.
- Reference the runtime profile.
- Record execution status.
- Associate produced evidence.
- Preserve diagnostics.

One collection execution may produce multiple evidence records.

### 6.2 CollectionOperation

**Type:** Value object or child entity, depending on lifecycle requirements.

Responsibilities:

- Describe an individual collection activity.
- Identify the operation type.
- Record target and configuration.
- Reference operation outcomes.

A collection execution may contain multiple operations.

### 6.3 TLSHandshakeObservation

**Type:** Typed evidence payload

Responsibilities:

- Represent one negotiated TLS connection.
- Associate protocol, cipher and key-establishment observations.
- Reference the peer certificate.
- Record certificate verification results.
- Preserve connection identity.

All negotiated properties must originate from the same connection.

### 6.4 TLSCapabilityProbe

**Type:** Collection operation

Responsibilities:

- Conduct a controlled TLS capability test.
- Record client configuration.
- Record requested protocol or group.
- Record the probe outcome.
- Preserve diagnostic information.
- Reference the runtime performing the probe.

A capability probe is distinct from the primary TLS handshake.

## 7. Runtime Domain

### 7.1 RuntimeProfile

**Type:** Immutable entity or versioned snapshot

**Identity:** `runtime_id`

Responsibilities:

- Identify the collection environment.
- Record operating system and architecture.
- Record Python implementation and version.
- Record SSL backend and OpenSSL version.
- Record relevant cryptographic library versions.
- Reference discovered runtime capabilities.

Runtime profiles are snapshots, not live representations of an environment.

### 7.2 RuntimeCapabilities

**Type:** Immutable value object

Responsibilities:

- Describe available collection APIs.
- Describe locally available protocol support.
- Describe locally available cryptographic groups.
- Describe configurable cryptographic mechanisms.
- Identify unavailable collection operations.

Runtime capabilities describe the collector, not remote endpoint capabilities.

## 8. Standards Domain

### 8.1 StandardsReference

**Type:** Entity

**Identity:** `reference_id`

Represents a stable standards document identity.

### 8.2 StandardsEdition

**Type:** Immutable entity or versioned publication record

Responsibilities:

- Identify a specific publication revision.
- Record publication and effective dates.
- Record publication status.
- Reference superseded or updated editions.

Historical editions must remain available.

### 8.3 StandardsProvision

**Type:** Entity within a standards edition

**Identity:** `provision_id`

Responsibilities:

- Identify a specific publication section or requirement.
- Describe its applicability.
- Support traceability to assessment rules.

### Relationships

| Relationship | Cardinality |
|---|---|
| StandardsReference → StandardsEdition | One-to-many |
| StandardsEdition → StandardsProvision | One-to-many |
| PolicyRuleVersion → StandardsProvision | Many-to-many |

A provision must always identify its originating standards edition.

## 9. Assessment Domain

### 9.1 PolicyIdentity

**Type:** Entity

**Identity:** `policy_id`

Represents a stable assessment policy identity.

Its versions change independently of its identity.

### 9.2 PolicyVersion

**Type:** Immutable entity

Responsibilities:

- Define a specific policy specification.
- Record objective, scope and exclusions.
- Reference its assessment rules.
- Identify its effective period.
- Preserve its publication status.

### 9.3 PolicyRuleIdentity

**Type:** Entity

**Identity:** `rule_id`

Represents the stable identity of an assessment rule.

### 9.4 PolicyRuleVersion

**Type:** Immutable entity

Responsibilities:

- Define one version of a rule.
- Identify required evidence.
- Define evaluation requirements.
- Preserve rationale.
- Reference applicable standards provisions.

Each rule version belongs to exactly one policy version.

### 9.5 AssessmentContext

**Type:** Value object

Responsibilities:

- Supply assessment scope.
- Reference relevant assets and evidence.
- Identify selected policy versions.
- Supply applicable standards profiles.
- Supply organizational context.
- Establish the assessment timestamp.

It must not depend directly on collector-specific result models.

### 9.6 AssessmentRun

**Type:** Immutable entity

**Identity:** `assessment_run_id`

Responsibilities:

- Identify one assessment execution.
- Record assessment scope.
- Preserve policy version snapshots.
- Preserve standards edition references.
- Reference the evidence evaluated.
- Record execution runtime and methodology.
- Associate policy execution results.

### 9.7 PolicyResult

**Type:** Immutable entity within an assessment run

Responsibilities:

- Record execution of one policy version.
- Record execution status.
- Associate assessment findings.
- Record limitations and diagnostics.

### 9.8 AssessmentFinding

**Type:** Immutable entity

**Identity:** `finding_id`

Responsibilities:

- Record one assessment conclusion.
- Identify affected assets.
- Identify the originating policy and rule versions.
- Record classification and rationale.
- Reference supporting evidence.
- Reference applicable standards provisions.
- Preserve limitations.

A finding must not depend on mutable policy or standards definitions.

## 10. Risk and Modernization Domain

### 10.1 RiskAssessment

**Type:** Entity

**Identity:** `risk_id`

Responsibilities:

- Associate technical findings with organizational context.
- Evaluate exposure and potential consequences.
- Record risk rationale.
- Support migration prioritization.
- Preserve the assumptions underlying risk decisions.

### 10.2 ModernizationPlan

**Type:** Entity

**Identity:** `plan_id`

Responsibilities:

- Record modernization objectives.
- Reference affected assets and findings.
- Identify proposed cryptographic replacements.
- Track migration activities.
- Record validation requirements.
- Monitor residual exposure.

Modernization plans must remain separate from technical assessment findings.

## 11. Entity Relationships

The principal cardinalities are:

| Parent | Child | Cardinality |
|---|---|---|
| Organization | Inventory | 1:N |
| Inventory | CryptographicAsset | 1:N |
| CryptographicAsset | AssetIdentifier | 1:N |
| CryptographicAsset | AssetRelationship | 1:N participation |
| CryptographicAsset | EvidenceRecord | 1:N |
| CollectionExecution | CollectionOperation | 1:N |
| CollectionExecution | EvidenceRecord | 1:N |
| RuntimeProfile | CollectionExecution | 1:N |
| StandardsReference | StandardsEdition | 1:N |
| StandardsEdition | StandardsProvision | 1:N |
| PolicyIdentity | PolicyVersion | 1:N |
| PolicyVersion | PolicyRuleVersion | 1:N |
| AssessmentRun | PolicyResult | 1:N |
| PolicyResult | AssessmentFinding | 1:N |
| AssessmentFinding | EvidenceRecord | N:M |
| PolicyRuleVersion | StandardsProvision | N:M |
| RiskAssessment | AssessmentFinding | N:M |

References between separate aggregates should generally use identifiers rather than direct object ownership.

## 12. Aggregate Boundaries

The initial domain should use these aggregate roots:

| Aggregate root | Owned objects |
|---|---|
| Organization | Organizational metadata |
| Inventory | Inventory metadata and membership |
| CryptographicAsset | Identifiers and asset specifications |
| AssetRelationship | Relationship metadata |
| EvidenceRecord | Evidence provenance and value |
| CollectionExecution | Collection operations and execution diagnostics |
| RuntimeProfile | Runtime capability snapshot |
| StandardsEdition | Standards provisions |
| PolicyVersion | Policy rule versions |
| AssessmentRun | Policy results and findings |
| RiskAssessment | Risk decision details |
| ModernizationPlan | Migration activities |

Aggregate boundaries must prevent accidental modification of historical evidence and assessment records.

## 13. Composition and Inheritance

The framework should favour composition.

`CryptographicAsset` should not become a large hierarchy of subclasses solely to represent different asset categories.

Instead:

- Common identity and lifecycle information belongs to `CryptographicAsset`.
- Type-specific attributes belong to `AssetSpecification`.
- Identifiers belong to `AssetIdentifier`.
- Relationships are separate entities.
- Evidence remains independently identifiable.

Inheritance should be introduced only where genuinely shared behaviour or substitutability requires it.

## 14. Immutability and Lifecycle

The following objects should be immutable after finalization:

- EvidenceRecord.
- RuntimeProfile.
- StandardsEdition.
- StandardsProvision.
- PolicyVersion.
- PolicyRuleVersion.
- AssessmentRun.
- AssessmentFinding.

Organizational assets, inventory membership and modernization plans may evolve through controlled updates.

Historical changes should be recorded rather than silently replacing prior states.

## 15. Serialization Boundaries

The domain model must not depend directly on:

- JSON field names.
- CycloneDX component objects.
- Database ORM entities.
- YAML configuration structures.
- Reporting templates.

Dedicated adapters will translate between domain objects and external formats.

This allows the internal architecture to evolve while preserving interoperability.

## 16. Design Constraints

The implementation must enforce the following constraints:

1. Every asset belongs to an identifiable inventory scope.
2. Every evidence record preserves its provenance.
3. A collection execution references the runtime used.
4. Negotiated TLS properties belong to one handshake observation.
5. Capability probes remain separate from primary handshake observations.
6. Every policy rule version belongs to exactly one policy version.
7. Every finding references its originating rule version.
8. Every standards provision belongs to one standards edition.
9. Assessment snapshots preserve historical definitions.
10. Evidence and findings cannot be silently overwritten.
11. Runtime capabilities cannot be used as proof of remote endpoint capabilities.
12. Private cryptographic material is not collected by default.

## 17. Implementation Direction

The specification guides the subsequent Python model design.

The initial implementation should prioritize:

1. Asset and inventory entities.
2. Asset identifiers and relationships.
3. Evidence and provenance.
4. Collection execution and operation models.
5. Runtime profiles and capabilities.
6. Standards editions and provisions.
7. Policy and rule versioning.
8. Assessment execution and findings.
9. Risk and modernization models.

These models must be introduced incrementally and integrated with the existing implementation through controlled migrations.

**Guiding principle:** Entity identity, ownership, lifecycle and relationships must be established before implementation-specific classes and storage structures are designed.
