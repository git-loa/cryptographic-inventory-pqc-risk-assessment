# Research and Development Plan

## Cryptographic Inventory, Security Assurance and Modernization Framework

**Project:** Cryptographic Inventory and PQC Risk Assessment
**Research baseline:** November 9, 2026
**Status:** Proposed
**Development approach:** Research-driven, incremental and modular

---

# 1. Research Purpose

The purpose of this research is to establish the technical, mathematical, architectural and standards foundations for an extensible cryptographic assessment framework.

The framework will support the discovery, inventory, assessment and management of cryptographic assets throughout their operational lifecycles.

It will address:

- Cryptographic discovery and inventory.
- Cryptographic configuration and implementation assurance.
- Cryptographic key establishment and key management.
- Randomness and entropy assurance.
- Post-quantum cryptography readiness.
- Cryptographic agility and interoperability.
- Cryptographic modernization and continuous assurance.

PQC migration is an important application of the framework, but its intended usefulness extends beyond the initial migration to post-quantum cryptography.

## 1.1 Research objective

Establish a defensible and extensible architecture that can:

1. Discover cryptographic assets across different computing environments.
2. Collect structured, verifiable cryptographic evidence.
3. represent cryptographic assets and dependencies using established inventory standards.
4. Evaluate cryptographic configurations against versioned standards and assessment requirements.
5. Identify cryptographic weaknesses and modernization requirements.
6. Support post-quantum migration planning and prioritization.
7. Monitor cryptographic changes and support continuous security assessment.

# 2. Research Questions

The research will address eight fundamental questions.

| ID | Research question |
|---|---|
| RQ1 | What cryptographic assets should organizations discover and maintain in their inventories? |
| RQ2 | What evidence is required to assess the security of those assets reliably? |
| RQ3 | How can evidence be collected across different operating systems, cryptographic libraries and implementations? |
| RQ4 | How should cryptographic assets, relationships and dependencies be represented interoperably? |
| RQ5 | How can assessment decisions remain traceable to changing standards and technical requirements? |
| RQ6 | How should cryptographic risks and PQC migration priorities be evaluated? |
| RQ7 | How can organizations achieve cryptographic agility and replace mechanisms without unacceptable operational disruption? |
| RQ8 | How can cryptographic inventories and assessment results remain current throughout an organization's operational lifecycle? |

These questions will guide the research, architecture and implementation.

# 3. Research Principles

The following principles will govern the project.

**Evidence-driven assessment:** Assessment conclusions must be supported by collected evidence or explicitly identified declarations.

**Separation of responsibilities:** Collection, inventory, assessment, risk analysis and reporting must remain distinct.

**Standards traceability:** Assessment rules must identify their supporting standards, provisions, versions and rationales.

**Runtime adaptability:** Collection methods must accommodate differences in Python, OpenSSL, cryptographic libraries and operating systems.

**Interoperability:** The framework should support established inventory standards and external tools.

**Reproducibility:** Historical assessments must retain the policy, methodology and collection environment used.

**Security by design:** Collectors must protect credentials, private keys and sensitive cryptographic material.

**Continuous modernization:** The framework must remain useful as cryptographic algorithms, standards and organizational requirements evolve.

# 4. Research Workstreams

The research will be organized into nine workstreams.

## WS1 — Cryptographic Discovery and Asset Classification

### Objective

Investigate the types of cryptographic assets used across enterprise computing environments and determine how they can be discovered and classified.

### Research areas

- TLS and other secure communication protocols.
- Public Key Infrastructure and digital certificates.
- Cryptographic algorithms and parameters.
- Cryptographic libraries and dependencies.
- Key-establishment mechanisms.
- Key-management systems and HSMs.
- Random bit generators and entropy sources.
- Cloud cryptographic services.
- Hardware and firmware cryptographic capabilities.
- Third-party cryptographic dependencies.

### Research questions

1. What constitutes a cryptographic asset?
2. How should assets be uniquely identified?
3. How should assets be related to applications, systems and vendors?
4. Which assets can be discovered remotely?
5. Which require local inspection or organizational documentation?
6. How should unknown, unavailable and unverified assets be represented?

### Deliverable

`docs/architecture/cryptographic-asset-taxonomy.md`

---

## WS2 — Evidence Collection and Canonical Data Model

### Objective

Establish a common evidence representation for all collection modules.

### Research areas

- Observed evidence.
- Capability evidence.
- Declared evidence.
- Derived evidence.
- Collection provenance.
- Evidence validation.
- Diagnostic information.
- Collection limitations.
- Evidence versioning.

The framework must distinguish:

| Evidence category | Example |
|---|---|
| Observed | TLS 1.3 negotiated during a handshake |
| Capability | TLS 1.2 successfully accepted during a controlled probe |
| Declared | Vendor claims support for ML-KEM |
| Derived | Cryptographic algorithm classified as quantum-vulnerable |
| Runtime | Python 3.15.2 using OpenSSL 3.5.9 |

### Research questions

1. What constitutes sufficient evidence for an assessment?
2. How should evidence sources be authenticated?
3. How should evidence obtained from separate connections be distinguished?
4. How should missing or inconclusive evidence affect assessment?
5. How should historical observations be preserved?
6. How can multiple collectors produce consistent evidence?

### Deliverables

- `docs/architecture/evidence-model.md`
- Canonical evidence data contract.
- Evidence provenance specification.

---

## WS3 — Runtime and Cryptographic Capability Management

### Objective

Investigate how differences in execution environments affect cryptographic discovery and assessment.

This workstream follows directly from the Python and OpenSSL experiments.

### Research areas

- Python implementations and versions.
- OpenSSL versions and providers.
- Python SSL interfaces.
- PyOpenSSL and other cryptographic libraries.
- Available TLS protocol versions.
- Available cryptographic algorithms and groups.
- ML-KEM and hybrid TLS capabilities.
- Platform trust stores.
- Cryptographic module configuration.
- Runtime compatibility.

### Important experimental observations

| Environment | Python | OpenSSL | Negotiated group visibility |
|---|---|---|---|
| Windows original environment | 3.12 | 3.0.11 | Not directly exposed |
| Windows experimental environment | 3.15.2 | 3.5.9 | Available |
| Kali WSL | — | 3.6.3 | OpenSSL CLI reports negotiated group |
| Ubuntu Server | — | 3.5.5 | OpenSSL CLI reports negotiated group |

### Research questions

1. Which capabilities are available through each supported Python SSL implementation?
2. How can runtime capabilities be detected automatically?
3. How can the framework collect negotiated groups from a single TLS connection?
4. How should unsupported collection capabilities be represented?
5. How can compatibility be maintained across Python and OpenSSL releases?
6. How should cryptographic library upgrades trigger regression testing?

### Deliverables

- `docs/architecture/runtime-capabilities.md`
- Runtime capability model.
- Python/OpenSSL compatibility matrix.
- Runtime detection specification.

---

## WS4 — CycloneDX and Cryptographic Inventory Interoperability

### Objective

Investigate how the framework will represent, import, export and exchange cryptographic inventory information.

### Research areas

- CycloneDX 1.7.
- ECMA-424, second edition.
- Cryptographic components and assets.
- Cryptographic algorithms and parameters.
- Certificates and key material metadata.
- Cryptographic dependencies.
- Asset relationships.
- External references.
- Evidence and attestations.
- CBOM validation and interoperability.

ECMA-424 defines the CycloneDX 1.7 BOM specification, including cryptographic artefacts, dependencies and supporting evidence.

### Research questions

1. Which internal assets map directly to CycloneDX concepts?
2. How should relationships between cryptographic assets be represented?
3. Which observations require additional native metadata?
4. How should incomplete CBOM documents be handled?
5. How should externally generated CBOM documents be validated?
6. How can inventory changes be compared over time?

### Architectural decision

CycloneDX will be an external interoperability format.

The framework will maintain its own canonical evidence and inventory models.

### Deliverables

- `docs/architecture/interoperability.md`
- CycloneDX mapping specification.
- CBOM import/export requirements.

---

## WS5 — Standards Research and Assessment Methodology

### Objective

Establish an adaptable standards-based assessment framework.

### Research areas

- NIST publications.
- IETF RFCs and Best Current Practice documents.
- FIPS cryptographic standards.
- Canadian Centre for Cyber Security guidance.
- Cryptographic module validation.
- Industry security requirements.
- Publication versions and errata.
- Standards supersession and withdrawal.
- Policy and rule versioning.

### Research questions

1. Which standards apply to each assessment policy?
2. Which provisions contain normative requirements?
3. Which publications provide recommendations rather than mandatory requirements?
4. How should conflicting recommendations be resolved?
5. How should standards changes affect assessment rationales?
6. How can historical assessment decisions remain reproducible?

### Deliverables

- `docs/standards-reference.md`
- Standards registry specification.
- Policy versioning specification.
- Assessment methodology.

The framework must distinguish between standards requirements, recommendations, organizational baselines and project-specific classifications.

A published standards update must not automatically change assessment results.

---

## WS6 — Cryptographic Security and PQC Assessment

### Objective

Research the technical requirements and evidence necessary for evaluating cryptographic mechanisms.

### Research areas

**Classical cryptography**

- RSA.
- Elliptic-curve cryptography.
- Diffie–Hellman.
- Symmetric encryption.
- Hash functions.
- Digital signatures.
- Cryptographic module assurance.

**Post-quantum cryptography**

- ML-KEM.
- ML-DSA.
- SLH-DSA.
- Hybrid key establishment.
- Hybrid authentication.
- Cryptographic parameter sets.
- Performance and interoperability.
- PQC migration requirements.

**Randomness and entropy**

- Entropy sources.
- Min-entropy.
- DRBG mechanisms.
- Seeding and reseeding.
- Random bit generator constructions.
- Health testing.

### Research questions

1. How should cryptographic strength be assessed?
2. How should quantum-vulnerable algorithms be identified?
3. How should hybrid cryptographic mechanisms be classified?
4. How should algorithm and module validation be established?
5. What evidence is necessary to assess entropy and DRBG implementations?
6. How should changes in cryptographic recommendations be incorporated?

### Deliverable

Technical assessment specifications for A1–A6.

---

## WS7 — Cryptographic Agility and Interoperability

### Objective

Investigate how organizations can replace cryptographic mechanisms throughout their infrastructure.

### Research areas

- Replaceable cryptographic implementations.
- Cryptographic APIs and abstractions.
- Algorithm negotiation.
- Protocol interoperability.
- Application dependencies.
- Vendor support.
- Performance constraints.
- Migration rollback.
- Hybrid deployment.
- Software and hardware compatibility.

NIST CSWP 39upd1 provides important guidance for this workstream.

### Research questions

1. How can cryptographic dependencies be identified?
2. What makes a cryptographic implementation replaceable?
3. How can migration compatibility be measured?
4. How should vendor dependencies be assessed?
5. How can organizations validate replacement mechanisms?
6. How should agility be evaluated independently of the algorithm's security?

### Deliverable

Cryptographic agility assessment specification for A8.

---

## WS8 — PQC Exposure, Risk and Migration Prioritization

### Objective

Establish a defensible method for identifying cryptographic exposure and prioritizing modernization.

### Research areas

- Harvest-now-decrypt-later exposure.
- Data sensitivity.
- Information protection lifetime.
- System criticality.
- Quantum-vulnerable algorithms.
- Cryptographic dependencies.
- Vendor readiness.
- Migration feasibility.
- Residual exposure.
- Migration validation.

NIST IR 8547 provides an important reference for this workstream.

### Research questions

1. How should quantum-vulnerable dependencies be identified?
2. How should information sensitivity influence migration priority?
3. How should information lifetime affect risk?
4. How should migration feasibility be assessed?
5. How should residual exposure be recorded?
6. How should migration completion be verified?
7. How should new cryptographic discoveries affect existing migration plans?

### Deliverable

PQC exposure and migration prioritization methodology for A9.

---

## WS9 — Continuous Cryptographic Assurance

### Objective

Investigate how the framework can remain useful after initial cryptographic assessments and PQC migration.

### Research areas

- Periodic cryptographic discovery.
- Configuration drift.
- CBOM comparison.
- Certificate and key lifecycle changes.
- Cryptographic library updates.
- Standards-change monitoring.
- Policy reassessment.
- Vendor change notifications.
- Migration progress monitoring.
- Residual-risk management.

### Research questions

1. How can changes in cryptographic assets be detected?
2. How can standards changes identify affected assets and policies?
3. When should an assessment be repeated?
4. How should historical findings be compared?
5. How should organizations verify migration completion?
6. How can reassessment be performed without unnecessary network scanning?

### Deliverable

Continuous cryptographic assurance architecture.

---

# 5. Assessment Policy Research

The framework will investigate nine distinct policy areas.

The catalogue below establishes the initial research boundaries. Final responsibilities will be confirmed through the collection requirements and overlap analysis.

| ID | Policy | Primary responsibility |
|---|---|---|
| A1 | TLS Protocol Configuration Assessment | Protocol configuration and negotiation |
| A2 | PKI and Digital Trust Assurance | Certificate trust, identity and trust infrastructure |
| A3 | Cryptographic Algorithm and Module Assurance | Algorithm, parameter and implementation suitability |
| A4 | Key Establishment and KEM Security | Establishment of cryptographic shared secrets |
| A5 | Cryptographic Key Management and Custody | Operational key protection and lifecycle management |
| A6 | Random Bit Generation and Entropy Assurance | Entropy, DRBG and random bit generator assurance |
| A7 | Cryptographic Inventory and Supply-Chain Visibility | Inventory coverage, dependencies and supplier transparency |
| A8 | Cryptographic Agility and Interoperability | Ability to replace and integrate cryptographic mechanisms |
| A9 | PQC Exposure and Migration Prioritization | Organizational quantum exposure and migration priority |

Every policy must have:

- Objective.
- Scope.
- Exclusions.
- Assessment dimensions.
- Required evidence.
- Collection limitations.
- Rules and classification logic.
- Standards references.
- Policy version.

A finding must belong to one policy and rule, even when several policies consume the same evidence.

---

# 6. Standards Research Baseline

The initial research should prioritize the following authoritative publications.

| Area | Publications | Research purpose |
|---|---|---|
| TLS | RFC 9846, RFC 8996, RFC 9325, RFC 9852, RFC 10015 | TLS protocol security and configuration |
| Hybrid TLS | RFC 9954, RFC 10024 | Hybrid key agreement |
| PQC algorithms | FIPS 203, FIPS 204, FIPS 205 | ML-KEM, ML-DSA and SLH-DSA |
| PQC transition | NIST IR 8547 | Migration planning |
| Key management | NIST SP 800-57 | Cryptographic key lifecycle |
| Entropy and randomness | NIST SP 800-90A, 800-90B, 800-90C | DRBG and entropy assurance |
| Module validation | FIPS 140-3 and CMVP | Cryptographic module assurance |
| Cryptographic agility | NIST CSWP 39upd1 | Algorithm replacement and modernization |
| Canadian guidance | ITSP.40.111 Version 5 | Canadian cryptographic requirements |
| Cryptographic inventory | CycloneDX 1.7 / ECMA-424 | CBOM interoperability |

### Important research status considerations

As of November 9, 2026:

- RFC 9846 supersedes RFC 8446 as the current TLS 1.3 specification. Our TLS references must reflect this update.
- RFC 9852 and RFC 10015 update RFC 9325.
- RFC 10024 specifies hybrid TLS 1.3 key-establishment mechanisms.
- NIST IR 8547 was finalized on October 27, 2026.
- Canadian ITSP.40.111 Version 5 took effect on May 29, 2026.
- FIPS 203 and FIPS 204 have published errata or potential-update notices. The framework must track these rather than assuming that a publication remains unchanged.
- NIST SP 800-90C was finalized in September 2025.
- SP 800-57 Part 1 Rev. 5 remains an important published reference; its Revision 6 public-draft status should be monitored rather than treating a draft as a final requirement.

Every standards entry must be checked for current status, applicable provisions, errata and supersession before it is used in an assessment rule.

---

# 7. Research Methodology

Research will use five complementary methods.

### 7.1 Standards analysis

Examine authoritative publications and extract applicable requirements, recommendations, limitations and implementation guidance.

Every extracted requirement should have a source reference and publication version.

### 7.2 Technical literature review

Examine cryptographic research, security engineering literature, technical reports and recognized implementation guidance.

Prioritize peer-reviewed work, IETF publications and official NIST documentation.

### 7.3 Experimental validation

Use controlled laboratory environments to validate technical assumptions.

The initial laboratory consists of:

- Windows scanner environment.
- Kali WSL TLS endpoint.
- Ubuntu Server TLS endpoint.
- Python 3.12 environment.
- Python 3.15.2 environment.
- Multiple OpenSSL versions.

Experiments should record:

- Software versions.
- Configuration.
- Inputs.
- Observed results.
- Expected results.
- Limitations.
- Reproducibility instructions.

### 7.4 Data-model and interoperability research

Examine CycloneDX CBOM modelling and external cryptographic inventory sources.

Validate proposed mappings against the actual specification and schema.

### 7.5 Implementation-driven evaluation

Implement small prototypes where documentation alone cannot establish feasibility.

Each prototype must have explicit acceptance criteria and automated tests.

---

# 8. Development Phases and Deliverables

The research workstreams will be completed through the following development phases.

| Phase | Focus | Main deliverable |
|---|---|---|
| 1 | Requirements and architecture | Approved architecture and collection requirements |
| 2 | Evidence architecture | Canonical evidence model |
| 3 | Runtime adaptability | Runtime and capability model |
| 4 | TLS collection | Refactored TLS collector |
| 5 | Capability probing | Controlled protocol and group probes |
| 6 | Endpoint assessment | A1–A4 foundations |
| 7 | Inventory interoperability | CycloneDX CBOM integration |
| 8 | Internal cryptographic discovery | A5–A7 foundations |
| 9 | Agility and migration | A8–A9 foundations |
| 10 | Continuous assurance | Change detection and reassessment |

Each phase must have a documented completion review before proceeding.

---

# 9. Initial Implementation Scope

The first major release will establish a reliable TLS-based cryptographic inventory and assessment capability.

It should support:

1. TLS endpoint collection.
2. Protocol and cipher-suite evidence.
3. Negotiated key-establishment group.
4. Certificate metadata and verification evidence.
5. Runtime provenance.
6. Controlled TLS protocol probes.
7. A1–A4 assessment foundations.
8. Native JSON evidence persistence.
9. Initial CycloneDX CBOM export.
10. Markdown and HTML assessment reporting.

It must not claim to provide a complete enterprise cryptographic inventory or full organizational PQC readiness assessment.

Those capabilities require additional collectors and organizational evidence.

---

# 10. Research and Development Checklist

The following checklist will guide our immediate work.

## Phase 1 — Research Foundation

- [ ] Review the overall project objectives.
- [ ] Validate the nine policy boundaries.
- [ ] Identify target organizational use cases.
- [ ] Establish the cryptographic asset taxonomy.
- [ ] Define collection scope and limitations.
- [ ] Identify authoritative standards.
- [ ] Establish research documentation structure.
- [ ] Record major architectural assumptions.

## Phase 2 — Evidence Architecture

- [ ] Define observed evidence.
- [ ] Define capability evidence.
- [ ] Define declared evidence.
- [ ] Define derived evidence.
- [ ] Define runtime provenance.
- [ ] Establish evidence identifiers.
- [ ] Define evidence lifecycle and status.
- [ ] Define evidence versioning.
- [ ] Define asset relationships.
- [ ] Define evidence validation requirements.

## Phase 3 — Runtime and Capability Management

- [ ] Research Python SSL API differences.
- [ ] Research OpenSSL provider and algorithm capabilities.
- [ ] Define runtime detection requirements.
- [ ] Define cryptographic capability discovery.
- [ ] Establish compatibility testing.
- [ ] Define unsupported-capability handling.
- [ ] Define runtime provenance requirements.

## Phase 4 — Collection Architecture

- [ ] Review existing TLS collection implementation.
- [ ] Identify changes required for single-connection evidence.
- [ ] Define controlled protocol probes.
- [ ] Define key-establishment capability probes.
- [ ] Define certificate collection responsibilities.
- [ ] Define collector interfaces.
- [ ] Define diagnostic and failure handling.
- [ ] Establish integration test scenarios.

## Phase 5 — Inventory and CBOM

- [ ] Review CycloneDX 1.7.
- [ ] Study ECMA-424.
- [ ] Define internal cryptographic inventory models.
- [ ] Map cryptographic assets to CBOM concepts.
- [ ] Define asset relationships and dependencies.
- [ ] Define CBOM export requirements.
- [ ] Define CBOM import requirements.
- [ ] Establish schema validation tests.

## Phase 6 — Standards and Assessment

- [ ] Establish standards registry.
- [ ] Define policy metadata.
- [ ] Define rule-level standards references.
- [ ] Define rationale management.
- [ ] Define policy and rule versioning.
- [ ] Establish historical assessment requirements.
- [ ] Finalize A1–A4 specifications.
- [ ] Research A5–A9 evidence requirements.
- [ ] Define standards-change review procedures.

## Phase 7 — Cryptographic Modernization

- [ ] Research PQC migration prioritization.
- [ ] Research cryptographic agility assessment.
- [ ] Research key lifecycle assurance.
- [ ] Research random bit generation assurance.
- [ ] Research cryptographic module validation.
- [ ] Research vendor cryptographic assurance.
- [ ] Define continuous assurance requirements.

## Phase 8 — Validation and Release

- [ ] Establish automated test coverage.
- [ ] Validate collection accuracy.
- [ ] Validate standards traceability.
- [ ] Validate CBOM interoperability.
- [ ] Validate runtime compatibility.
- [ ] Review security and privacy controls.
- [ ] Update documentation.
- [ ] Conduct release review.

---

# 11. Expected Research Outcomes

The research should produce the following foundational documents:

```text
docs/
│
├── architecture.md
├── assessment-methodology.md
├── policy-catalogue.md
├── standards-reference.md
│
├── architecture/
│   ├── research-and-development-plan.md
│   ├── cryptographic-asset-taxonomy.md
│   ├── collection-requirements.md
│   ├── evidence-model.md
│   ├── runtime-capabilities.md
│   ├── interoperability.md
│   └── continuous-assurance.md
│
├── policies/
│   ├── A1.md
│   ├── A2.md
│   ├── A3.md
│   ├── A4.md
│   ├── A5.md
│   ├── A6.md
│   ├── A7.md
│   ├── A8.md
│   └── A9.md
│
└── decisions/
    ├── ADR-001-evidence-model.md
    ├── ADR-002-runtime-capabilities.md
    ├── ADR-003-cyclonedx-integration.md
    └── ADR-004-policy-versioning.md
```

The documents will evolve as research findings and implementation experience refine the architecture.

---

# 12. Project Success Criteria

The framework will be considered successful when it can:

1. Discover cryptographic assets through independent collectors.
2. Produce consistent, verifiable and traceable evidence.
3. Explain collection limitations and runtime dependencies.
4. Represent cryptographic inventories using established standards.
5. Import and export interoperable CBOM documents.
6. Assess cryptographic mechanisms against versioned requirements.
7. Explain every assessment finding through evidence, rules and standards references.
8. Accommodate changes in cryptographic libraries and standards.
9. Support PQC migration assessment and cryptographic modernization.
10. Maintain useful inventories and assessments after migration.

The framework must prioritize defensible technical conclusions over the quantity of features implemented.

# 13. Long-Term Vision

The ultimate objective is to establish a framework that supports continuous cryptographic asset management.

PQC migration will be one major modernization activity.

After migration, the same framework should continue supporting:

- Cryptographic algorithm transitions.
- Certificate and key lifecycle management.
- Cryptographic implementation assurance.
- Standards and vulnerability monitoring.
- Dependency and vendor assessments.
- Cryptographic agility.
- Continuous inventory validation.
- Future cryptographic modernization.

The project should not depend on any particular algorithm, protocol, cryptographic library or standards revision.

Its enduring value will come from its ability to discover cryptographic assets, preserve evidence, evaluate changing requirements and support informed security decisions.

**Guiding principle: Build for continuous cryptographic assurance, not a single cryptographic transition.**
