# Domain Model Specification

**Project:** Cryptographic Inventory, Security Assurance and Modernization Framework

**Version:** 0.1.0

**Status:** Proposed

## 1. Purpose

This document describes the main concepts represented by the framework and how they relate to one another.

The framework helps organizations discover cryptographic assets, record supporting evidence, assess security configurations and plan cryptographic modernization, including migration to post-quantum cryptography (PQC).

The domain model is independent of collection tools, databases and external inventory formats.

## 2. Main Domains

The framework consists of the following domains:

| Domain | Responsibility |
|---|---|
| Organization and Inventory | Defines organizations and their inventory scope. |
| Assets | Represents systems, applications, services and cryptographic components. |
| Relationships | Records how assets are connected. |
| Evidence | Stores observations, declarations and derived information. |
| Collection | Records discovery activities and their results. |
| Runtime | Describes the environment used for collection. |
| Standards | Maintains standards and their requirements. |
| Assessment | Evaluates evidence against defined security requirements. |
| Risk and Modernization | Supports risk decisions and cryptographic migration planning. |

## 3. Organization and Inventory

An **Organization** represents an entity responsible for one or more inventories.

An **Inventory** defines the scope of assets being discovered and assessed.

An asset may belong to multiple inventories without creating duplicate asset records. Inventory membership is maintained separately from asset identity.

## 4. Asset Domain

The Asset domain represents identifiable entities or components that provide, use, store, process or depend on cryptographic functionality.

### Asset

An Asset represents a computing system, application, network service, software component, certificate, key reference, cryptographic module, randomness component or cryptographic service.

Every asset has a stable internal UUID, a primary classification, a name and an optional technical specification.

### AssetIdentifier

Represents an external identifier associated with an asset.

Examples include:

- Hostnames and IP addresses.
- Certificate fingerprints.
- Software package identifiers.
- Vendor or hardware identifiers.
- Cloud resource identifiers.

An identifier has a namespace and value, with optional issuer and validity timestamps. External identifiers do not replace the asset's internal UUID.

### AssetSpecification

Contains technical information specific to an asset category.

The initial specifications cover:

- Network endpoints.
- X.509 certificates.
- Software components.
- Cryptographic key references.

Additional specifications will be introduced as collection requirements are established.

### AssetLifecycle

Records the current lifecycle status of an asset, including its creation and last-update timestamps.

Changing an asset's lifecycle produces an updated asset instance while preserving its identity.

Asset lifecycle is separate from evidence freshness and collection status.

### AssetRelationship

Represents a directed connection between two assets.

The framework supports nine relationship types:

| Relationship | Meaning |
|---|---|
| HOSTS | Provides a deployment environment for another asset. |
| RUNS | Executes an application. |
| EXPOSES | Makes a network service available. |
| PRESENTS | Presents a certificate during communication. |
| USES | Directly uses another asset. |
| PROVIDES | Provides a cryptographic service. |
| DEPENDS_ON | Requires another asset to operate. |
| MANAGED_BY | Is operationally managed by another asset. |
| CONTAINS | Contains another asset as a component. |

Each relationship has a source and target. The framework checks whether their asset classifications are compatible.

Supporting evidence is required to establish that a relationship actually exists.

### Asset Identity Resolution

Identity resolution determines whether a newly discovered asset already exists in the inventory.

It considers identifiers, asset classification and supporting evidence.

Uncertain matches must be recorded for review rather than automatically merging assets.

## 5. Cryptographic Mechanisms

Cryptographic algorithms, protocols, cipher suites and parameter sets are distinct from organizational assets.

Examples include:

- RSA and ECDSA.
- AES-GCM and ChaCha20-Poly1305.
- SHA-256 and SHA-3.
- ML-KEM, ML-DSA and SLH-DSA.
- Hybrid key-establishment mechanisms.

A software component such as OpenSSL is an asset. RSA is a cryptographic mechanism supported or used by that asset.

Mechanism support and actual mechanism usage must be recorded separately.

This distinction is important for cryptographic inventories and CBOM generation.

## 6. Evidence Domain

Evidence records what the framework knows about an asset or another domain object.

Four evidence types are distinguished:

| Type | Meaning |
|---|---|
| Observed | Directly observed behaviour or configuration. |
| Capability | A demonstrated capability. |
| Declared | Information supplied by an organization or vendor. |
| Derived | Information produced through documented analysis. |

Each evidence record identifies its subject, property, value, source and observation time.

Evidence must retain its origin and known limitations.

Finalized evidence is immutable. New observations create new records rather than silently replacing historical information.

Evidence lifecycle is separate from collection outcome.

## 7. Collection Domain

Collection records how information is discovered.

A **CollectionExecution** represents one execution of a collector.

A **CollectionOperation** represents an individual activity within that execution.

An operation may produce zero or more evidence records.

TLS collection distinguishes:

- `TLSHandshakeObservation`: Records an actual negotiated TLS connection.
- `TLSCapabilityProbeResult`: Records the outcome of a controlled capability test.

Negotiated properties must come from the same identified handshake. Controlled probes must remain separate from ordinary connection observations.

Collection may succeed, partially complete, produce inconclusive results or fail.

A failed collection must not be interpreted as proof that an asset or capability does not exist.

## 8. Runtime Domain

A RuntimeProfile describes the environment used to perform collection.

It records relevant information such as:

- Operating system and architecture.
- Python implementation and version.
- SSL backend and OpenSSL version.
- Available cryptographic APIs and collection capabilities.

Local runtime capabilities must not be interpreted as proof of remote endpoint capabilities.

## 9. Standards Domain

The Standards domain maintains authoritative publications and their requirements.

A **StandardsReference** identifies a publication.

A **StandardsEdition** represents a particular revision.

A **StandardsProvision** represents an individual requirement or recommendation within that edition.

Historical editions remain available so that previous assessments can be understood and reproduced.

## 10. Assessment Domain

The Assessment domain evaluates evidence against defined, versioned security requirements.

Its main concepts are:

| Concept | Responsibility |
|---|---|
| PolicyIdentity | Identifies a policy. |
| PolicyVersion | Defines a particular version of a policy. |
| PolicyRuleIdentity | Identifies an assessment rule. |
| PolicyRuleVersion | Defines a particular version of a rule. |
| AssessmentContext | Supplies the assets, evidence and configuration for assessment. |
| AssessmentRun | Records an assessment execution. |
| PolicyResult | Records the outcome of a policy execution. |
| AssessmentFinding | Records an individual conclusion. |

Every finding must identify its originating rule version and supporting evidence.

Missing evidence must not automatically be treated as proof of security or insecurity.

## 11. Risk and Modernization

### RiskAssessment

Evaluates technical findings in the context of an organization's environment.

Considerations include:

- Data sensitivity.
- Information protection lifetime.
- System criticality.
- Cryptographic exposure.
- Migration feasibility.

Risk decisions must retain their assumptions and rationale.

### ModernizationPlan

Coordinates cryptographic replacement activities.

It identifies affected assets, proposed replacements, migration tasks, validation requirements and remaining risks.

This domain supports activities such as replacing vulnerable algorithms, improving cryptographic configurations and planning PQC migration.

## 12. Domain Principles

The framework follows these principles:

1. Every asset has a stable internal identity.
2. External identifiers do not replace internal asset identity.
3. Assets and their relationships are separate concepts.
4. Cryptographic mechanisms are not automatically treated as independent assets.
5. Evidence retains its source and observation history.
6. Collection outcomes are separate from evidence values.
7. Historical evidence and assessment results are preserved.
8. Assessment policies operate on canonical evidence, not collector-specific objects.
9. Domain concepts remain independent of databases and external formats.
10. Private keys and secret material are not collected as ordinary inventory data.

**Guiding principle:** Assets represent what exists; relationships describe how assets connect; evidence records what is known; collection explains how information was obtained; assessment evaluates that information; risk and modernization support organizational decisions.
