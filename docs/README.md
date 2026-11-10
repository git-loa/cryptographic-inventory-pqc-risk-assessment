# Documentation

**Cryptographic Inventory, Security Assurance and Modernization Framework**

This documentation describes the framework's architecture, cryptographic inventory capabilities, assessment methodology and modernization approach.

## Architecture

| Document | Description |
|---|---|
| [Overview](architecture/overview.md) | System architecture and main workflows |
| [Research and Development Plan](architecture/research-and-development-plan.md) | Research objectives, workstreams and roadmap |
| [Package Architecture](architecture/package-architecture.md) | Python package organization |
| [Dependency and Migration Strategy](architecture/dependency-and-migration-strategy.md) | Dependency boundaries and implementation migration |

## Domain Design

Located in [`architecture/domain/`](architecture/domain/).

| Document | Description |
|---|---|
| [Domain Model](architecture/domain/domain-model.md) | Fundamental domain concepts |
| [Entity Relationships](architecture/domain/entity-relationships.md) | Ownership and relationships |
| [Domain Class Design](architecture/domain/domain-class-design.md) | Python class responsibilities |
| [Entity Relationship Diagram](architecture/domain/entity-relationship-diagram.md) | Visual domain relationships |
| [Domain Class Diagram](architecture/domain/domain-class-diagram.md) | Visual class structure |

## Collection and Evidence

Located in [`architecture/collection/`](architecture/collection/).

| Document | Description |
|---|---|
| [Cryptographic Asset Taxonomy](architecture/collection/cryptographic-asset-taxonomy.md) | Asset classifications |
| [Collection Requirements](architecture/collection/collection-requirements.md) | Discovery and collection requirements |
| [Evidence Model](architecture/collection/evidence-model.md) | Evidence representation and provenance |
| [Runtime Capabilities](architecture/collection/runtime-capabilities.md) | Runtime and cryptographic capability detection |

## Interoperability and Modernization

| Document | Description |
|---|---|
| [CycloneDX CBOM](architecture/interoperability/cyclonedx-cbom.md) | Cryptographic inventory interoperability |
| [Continuous Assurance](architecture/modernization/continuous-assurance.md) | Ongoing cryptographic monitoring and modernization |

## Assessment and Standards

| Document | Description |
|---|---|
| [Assessment Methodology](assessment/assessment-methodology.md) | General assessment principles and methodology |
| [Assessment Policies](policies/) | Individual assessment policy specifications |
| [Standards Reference](standards/standards-reference.md) | Applicable standards and technical publications |

---

**Documentation principle:** Architecture, implementation requirements and assessment methodology are maintained separately to preserve clarity and traceability.
