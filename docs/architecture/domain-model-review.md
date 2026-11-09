# Domain Model Consistency Review

**Project:** Cryptographic Inventory, Security Assurance and Modernization Framework
**Version:** 0.1.0
**Status:** Accepted design decisions
**Date:** November 9, 2026

## 1. Purpose

This document records architectural refinements identified during the consistency review of:

- `domain-model.md`
- `entity-relationships.md`
- `domain-class-design.md`

The objective is to establish consistent domain terminology, ownership, relationships and modelling decisions before implementing Python classes.

These decisions supersede conflicting proposals in earlier specifications.

## 2. Decision 1 — General Asset Identity

### Previous proposal

The foundational entity was named `CryptographicAsset`.

### Accepted decision

Rename the foundational entity to `Asset`.

The framework must represent both general organizational assets and cryptographic assets.

Initial asset categories include:

- Computing systems.
- Applications.
- Network services.
- Software components.
- Certificates.
- Cryptographic key references.
- Cryptographic algorithms and implementations.
- Cryptographic modules.
- Randomness components.
- Cryptographic services.

### Design

`Asset` maintains common identity, classification and lifecycle information.

Type-specific information belongs in an associated `AssetSpecification`.

The framework will use composition rather than an extensive inheritance hierarchy.

### Rationale

Not every organizational asset is itself cryptographic, but it may host, implement or depend on cryptographic functionality.

The broader `Asset` abstraction supports dependency discovery and organizational inventory management.

## 3. Decision 2 — Inventory Membership

### Previous proposal

An asset was directly associated with one inventory.

### Accepted decision

Introduce `InventoryMembership` as an independent association entity.

The relationship becomes:

```text
Organization
     |
     | 1:N
     v
  Inventory
     |
     | 1:N
     v
InventoryMembership
     |
     | N:1
     v
    Asset
```

### Responsibilities

`InventoryMembership` records:

- Membership identifier.
- Inventory identifier.
- Asset identifier.
- Membership start time.
- Membership end time.
- Membership status.

### Rationale

An asset may legitimately appear in multiple inventory scopes without creating duplicate asset identities.

Membership history must be preserved.

## 4. Decision 3 — Evidence Classification and Collection Status

### Previous proposal

Evidence categories and collection statuses were defined, but their responsibilities were not sufficiently separated.

### Accepted decision

Evidence nature, evidence value, provenance, collection outcome and evidence lifecycle must be independent concepts.

#### Evidence nature

| Value | Meaning |
|---|---|
| observed | Directly observed system behaviour or configuration |
| capability | Demonstrated system capability |
| declared | Organization or vendor declaration |
| derived | Result of a documented transformation or analysis |

#### Collection outcomes

| Value | Meaning |
|---|---|
| succeeded | Collection operation completed successfully |
| partial | Some requested information was obtained |
| rejected_by_remote | Remote system explicitly rejected the operation |
| inconclusive | Result did not establish the intended conclusion |
| unsupported_by_client | Local collector could not perform the operation |
| timed_out | Operation exceeded its permitted duration |
| failed | Operation failed for another established reason |
| not_attempted | Operation was not executed |

Collection outcomes belong to collection operations, not automatically to EvidenceRecord.

#### Evidence lifecycle

An evidence record may have a lifecycle state such as:

- current
- superseded
- withdrawn

An unsuccessful probe must not create an invented observation.

Its outcome and diagnostic information belong to the corresponding collection operation.

### Evidence attributes

An EvidenceRecord should distinguish:

- Evidence identifier.
- Subject asset.
- Evidence nature.
- Property.
- Typed value.
- Provenance.
- Observation timestamp.
- Lifecycle status.
- Limitations.

Evidence quality and confidence must not be inferred solely from successful collection.

Where required, validation and corroboration information should be recorded independently.

## 5. Decision 4 — Standards Model

### Previous proposal

StandardsProvision was described inconsistently as both an entity and a value object.

### Accepted decision

Use the following structure:

```text
StandardsReference
       |
       | 1:N
       v
StandardsEdition
       |
       | 1:N
       v
StandardsProvision
```

Responsibilities:

**StandardsReference**

Maintains the stable publication identity, publisher and document identifier.

**StandardsEdition**

Represents a specific publication revision, publication status and relevant dates.

**StandardsProvision**

An immutable value object belonging to a specific standards edition.

It identifies a section, requirement, recommendation or other relevant provision.

### Rationale

A publication may have multiple editions, and each edition may contain multiple provisions.

Assessment rules must reference the specific edition and provision used.

Historical assessment results must not silently inherit newer standards interpretations.

## 6. Decision 5 — Policy and Rule Versioning

### Accepted decision

Separate stable policy and rule identities from their immutable versions.

The model is:

```text
PolicyIdentity
      |
      | 1:N
      v
PolicyVersion
      |
      | 1:N
      v
PolicyRuleVersion
      ^
      |
      | N:1
PolicyRuleIdentity
```

Each PolicyRuleVersion belongs to exactly one PolicyVersion.

A rule may have multiple historical versions.

A policy version must preserve its applicable rule versions.

### Rationale

This supports controlled changes to assessment classifications, rationales, evidence requirements and standards references.

Historical assessments must preserve the exact policy and rule versions that produced their findings.

## 7. Decision 6 — Immutability

### Accepted decision

Finalized evidence and historical assessment records must be immutable.

This includes:

- EvidenceRecord.
- RuntimeProfile.
- StandardsEdition.
- StandardsProvision.
- PolicyVersion.
- PolicyRuleVersion.
- AssessmentRun.
- AssessmentFinding.

Mutable organizational entities must use controlled state transitions.

Python `frozen=True` alone does not guarantee deep immutability.

Nested dictionaries, lists and mutable objects must therefore be avoided or protected through immutable value structures.

### Rationale

Historical evidence and assessment results provide the foundation for auditing, reproducibility and configuration-change detection.

Previously collected information must not be silently modified.

## 8. Consolidated Design Decisions

| ID | Area | Accepted decision |
|---|---|---|
| DMD-001 | Asset identity | Use the general `Asset` entity |
| DMD-002 | Inventory | Use independent `InventoryMembership` |
| DMD-003 | Evidence | Separate evidence nature, collection outcome and lifecycle |
| DMD-004 | Standards | Use reference, edition and provision layers |
| DMD-005 | Policies | Separate stable identity from immutable versions |
| DMD-006 | Rules | Each rule version belongs to exactly one policy version |
| DMD-007 | Immutability | Protect finalized evidence and historical assessments |
| DMD-008 | Asset specifications | Prefer composition over extensive inheritance |
| DMD-009 | Collection | Failed operations remain collection diagnostics rather than invented evidence |
| DMD-010 | Historical records | Preserve original assessment and standards references |

## 9. Impact on Subsequent Design

These decisions must be reflected in:

1. The final entity relationship diagram.
2. The domain class diagram.
3. The Python package architecture.
4. The canonical evidence contract.
5. The assessment execution model.
6. The persistence and serialization boundaries.
7. The CycloneDX integration specification.

Existing TLS collection and assessment models will be migrated incrementally.

No existing functionality should be discarded merely to satisfy the new organization.

## 10. Approval Status

The decisions recorded in this document establish the accepted direction for the next architectural design stage.

They do not authorize immediate source-code restructuring.

The next deliverable is the consolidated Entity Relationship Diagram, followed by the Domain Class Diagram.

**Guiding principle:** Maintain stable asset identities, immutable historical evidence, explicit ownership and independently versioned assessment requirements.
