# Domain Model Specification

**Project:** Cryptographic Inventory, Security Assurance and Modernization Framework

**Version:** 0.1.0

**Status:** Proposed

## 1. Purpose

The domain model defines the fundamental concepts underlying cryptographic discovery, inventory management, evidence collection, security assessment and cryptographic modernization.

It provides a technology-independent foundation for the framework. Collection tools, cryptographic libraries, storage implementations and external inventory formats interact with these concepts through defined interfaces.

## 2. Architectural Principles

The domain follows these principles:

1. Assets have stable internal identities independent of external identifiers.
2. Evidence preserves its subject, value, origin and provenance.
3. Collection activities are separate from the evidence they produce.
4. Runtime capabilities are distinct from remote system capabilities.
5. Assessment policies consume canonical evidence rather than collector-specific models.
6. Standards and assessment rules are independently versioned.
7. Historical evidence and assessment results remain reproducible.
8. Domain models are independent of persistence and external inventory formats.
9. Cryptographic secrets are not collected or stored by default.

## 3. Domain Overview

The framework consists of the following interconnected domains:

| Domain | Responsibility |
|---|---|
| Organization and Inventory | Defines organizational boundaries and asset inventories. |
| Assets | Represents systems, components, services and cryptographic objects. |
| Relationships | Represents dependencies and associations between assets. |
| Evidence | Records observations, declarations and derived information. |
| Collection | Records discovery and evidence collection activities. |
| Runtime | Describes collection environments and capabilities. |
| Standards | Maintains authoritative publications and provisions. |
| Assessment | Evaluates evidence against versioned policies and rules. |
| Risk and Modernization | Supports risk analysis and cryptographic replacement planning. |

## 4. Organization and Inventory

### Organization

Represents an organization responsible for one or more cryptographic inventories.

### Inventory

Defines an organizational scope for discovering, registering and assessing assets.

### InventoryMembership

Associates an asset with an inventory without duplicating its identity.

An asset may belong to multiple inventories.

```mermaid
erDiagram
    ORGANIZATION ||--o{ INVENTORY : maintains
    INVENTORY ||--o{ INVENTORY_MEMBERSHIP : contains
    ASSET ||--o{ INVENTORY_MEMBERSHIP : participates_in
```

## 5. Asset Domain

### Asset

Represents an identifiable computing system, application, service, software component or cryptographic object that provides, uses, stores or depends on cryptographic functionality.

Every asset has a stable internal UUID.

Principal attributes include:

- Asset identifier.
- Asset type.
- Name and description.
- External identifiers.
- Type-specific specification.
- Lifecycle status.
- Creation and update timestamps.

### AssetIdentifier

Represents a namespaced external identifier, such as a hostname, IP address, certificate fingerprint or software package identifier.

External identifiers do not replace internal asset identity.

### AssetSpecification

Contains attributes specific to an asset type.

Examples include network endpoints, certificates, software components, cryptographic keys, cryptographic modules and randomness components.

### AssetRelationship

Represents a directed relationship between two assets.

Examples include `hosts`, `runs`, `exposes`, `presents`, `uses`, `implements`, `depends_on` and `managed_by`.

Relationships have independent identities and may preserve historical validity and supporting evidence.

## 6. Evidence Domain

### EvidenceRecord

Represents a finalized observation, demonstrated capability, external declaration or derived result.

Evidence may describe an asset, organization, runtime or collection activity.

Evidence types:

| Type | Meaning |
|---|---|
| `observed` | Directly observed behaviour or configuration |
| `capability` | Demonstrated capability |
| `declared` | Information supplied by an organization or vendor |
| `derived` | Result of documented analysis or transformation |

An evidence record contains:

- Evidence identifier.
- Subject reference.
- Evidence type and property.
- Typed value.
- Provenance.
- Observation timestamp.
- Lifecycle status.
- Known limitations.

### EvidenceProvenance

Identifies the origin of evidence, including its source, collection operation, runtime or derivation process where applicable.

### EvidenceValue

Represents a semantically typed evidence payload, such as TLS observations, certificate metadata or software component information.

Evidence values must not rely on unrestricted, unvalidated dictionaries as their default representation.

Evidence lifecycle is distinct from collection outcome. Finalized evidence records are immutable; subsequent observations create new records.

## 7. Collection Domain

### CollectionExecution

Represents one execution of a collector. It records collector identity, version, runtime, timestamps, overall status and diagnostics.

### CollectionOperation

Represents an individual activity within a collection execution.

An execution may contain zero or more operations. An operation may produce zero or more evidence records.

Collection outcomes include success, partial completion, inconclusive results, unsupported client capabilities, timeouts and failures.

### TLS-specific observations

Two distinct concepts are required:

- `TLSHandshakeObservation`: Records one actual negotiated TLS connection.
- `TLSCapabilityProbeResult`: Records an independent controlled probe.

Negotiated protocol, cipher suite and key-establishment group must originate from the same identified handshake.

Capability probes must preserve their client configuration, outcome and limitations.

## 8. Runtime Domain

### RuntimeProfile

Represents an immutable snapshot of the collection environment.

It records:

- Operating system and architecture.
- Python implementation and version.
- SSL backend and OpenSSL version.
- Relevant cryptographic library versions.
- Runtime capability information.
- Capture timestamp.

### RuntimeCapabilities

Describes locally available APIs, cryptographic groups, protocols and collection methods.

**Local capabilities must never be interpreted as proof of remote endpoint capabilities.**

## 9. Standards Domain

### StandardsReference

Represents the stable identity of an authoritative publication, including publisher, document identifier and title.

### StandardsEdition

Represents a specific publication revision, including publication date, effective date, status and official URL.

### StandardsProvision

Represents an immutable requirement, recommendation or other relevant provision within a specific edition.

```mermaid
erDiagram
    STANDARDS_REFERENCE ||--o{ STANDARDS_EDITION : identifies
    STANDARDS_EDITION ||--o{ STANDARDS_PROVISION : contains
```

Historical editions remain available for assessment reproducibility.

## 10. Assessment Domain

The assessment domain interprets canonical evidence against versioned requirements.

| Concept | Responsibility |
|---|---|
| PolicyIdentity | Maintains a stable policy identity. |
| PolicyVersion | Defines an immutable policy specification. |
| PolicyRuleIdentity | Maintains a stable rule identity. |
| PolicyRuleVersion | Defines an immutable version of a rule. |
| AssessmentContext | Supplies assets, evidence and assessment configuration. |
| AssessmentRun | Represents an assessment execution. |
| PolicyResult | Records an individual policy execution. |
| AssessmentFinding | Records an individual assessment conclusion. |

Each rule version belongs to exactly one policy version.

Every finding identifies its originating rule version, affected assets, supporting evidence and applicable standards provisions.

```mermaid
flowchart TD
    A[Canonical Evidence] --> B[Assessment Context]
    B --> C[Assessment Run]
    C --> D[Versioned Policies]
    D --> E[Versioned Rules]
    E --> F[Assessment Findings]
    F --> G[Risk Analysis]
```

Policy execution status is independent of finding classification. A successfully executed policy may produce `unknown` findings when evidence is insufficient.

## 11. Risk and Modernization

### RiskAssessment

Evaluates technical findings against organizational context.

Relevant considerations include:

- Data sensitivity.
- Information protection lifetime.
- System criticality.
- Cryptographic exposure.
- Migration feasibility.

Risk decisions must preserve their assumptions and rationale.

### ModernizationPlan

Coordinates cryptographic replacement and modernization activities.

It identifies affected assets, proposed replacements, migration tasks, validation requirements and residual exposure.

Risk assessment and modernization remain separate from technical policy execution.

## 12. Domain Invariants

The implementation must enforce:

1. Every asset has a stable internal identity.
2. Inventory membership does not duplicate assets.
3. Evidence preserves its subject and provenance where applicable.
4. Collection outcomes are distinct from evidence values.
5. TLS negotiated properties belong to one identified handshake.
6. Scanner and target runtime information remain distinct.
7. Historical evidence and findings cannot be silently overwritten.
8. Every finding references its originating rule version.
9. Every rule version belongs to one policy version.
10. Standards provisions belong to a specific edition.
11. Missing evidence does not automatically imply security or insecurity.
12. Private keys and secret material are excluded from ordinary inventory evidence.

## 13. Interoperability and Implementation Boundaries

Domain objects remain independent of JSON, databases, Pydantic models and CycloneDX structures.

Dedicated adapters translate between domain objects and external representations.

CycloneDX provides inventory interoperability; it does not define the framework's internal domain model or assessment methodology.

Implementation details, including Python classes and interfaces, are specified separately in `domain-class-design.md`.

**Guiding principle:** Assets represent what exists; evidence represents what is known; collection records how knowledge was obtained; standards define applicable requirements; assessment interprets evidence; risk and modernization support organizational decisions.
