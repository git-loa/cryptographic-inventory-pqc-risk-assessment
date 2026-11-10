# Framework Architecture Overview

**Project:** Cryptographic Inventory, Security Assurance and Modernization Framework

**Version:** 0.1.0

**Status:** Proposed

## 1. Purpose

The framework provides a structured approach to discovering cryptographic assets, collecting evidence, assessing security requirements and supporting cryptographic modernization.

It is designed to support organizations throughout the lifecycle of their cryptographic infrastructure, including post-quantum cryptography migration.

## 2. System Architecture

The framework separates domain concepts, collection mechanisms, assessment policies and infrastructure implementations.

```mermaid
flowchart TD
    USER([Security Engineers / Organizations])
    CLI[Command Line Interface]
    APP[Application Services]

    subgraph CORE["Core Capabilities"]
        COL[Cryptographic Collection]
        INV[Asset Inventory]
        BOM[CycloneDX CBOM]
        ASM[Assessment Engine]
        STD[Standards Registry]
        RISK[Risk Analysis]
        MOD[Modernization Planning]
    end

    RT[Runtime Detection]
    INFRA[Infrastructure]
    REP[Reporting]

    USER --> CLI
    CLI --> APP

    APP --> COL
    APP --> INV
    APP --> BOM
    APP --> ASM
    APP --> RISK
    APP --> MOD
    APP --> REP

    RT --> COL
    COL --> INV
    INV --> BOM
    STD --> ASM
    ASM --> RISK
    RISK --> MOD

    INFRA -.-> APP
```

The domain model provides common representations for assets, relationships, evidence and assessment results.

## 3. Evidence Collection and Inventory

Independent collectors discover cryptographic assets and collect supporting evidence.

```mermaid
flowchart LR
    TLS[TLS Endpoints]
    PKI[Certificates / PKI]
    SW[Software Components]
    SYS[System Configuration]
    RNG[Randomness Sources]
    HSM[HSM / KMS]

    TLS --> COL[Collection Engine]
    PKI --> COL
    SW --> COL
    SYS --> COL
    RNG --> COL
    HSM --> COL

    RT[Runtime Profile] --> COL

    COL --> EV[Canonical Evidence]
    EV --> INV[Cryptographic Inventory]
    INV --> CBOM[CycloneDX CBOM]
```

Every observation should preserve its subject, source, timestamp, collection method and limitations.

Collectors do not make assessment decisions.

## 4. Security Assessment

The assessment engine evaluates canonical evidence against independently versioned policies, rules and standards.

```mermaid
flowchart TD
    EV[Canonical Evidence]
    CTX[Assessment Context]
    ENG[Assessment Engine]
    STD[Versioned Standards]

    EV --> CTX
    CTX --> ENG
    STD --> ENG

    ENG --> A1[A1: TLS Configuration]
    ENG --> A2[A2: PKI and Trust]
    ENG --> A3[A3: Algorithm Assurance]
    ENG --> A4[A4: Key Establishment]
    ENG --> A5[A5: Key Management]
    ENG --> A6[A6: Randomness]
    ENG --> A7[A7: Inventory]
    ENG --> A8[A8: Cryptographic Agility]
    ENG --> A9[A9: PQC Migration]

    A1 --> FIND[Assessment Findings]
    A2 --> FIND
    A3 --> FIND
    A4 --> FIND
    A5 --> FIND
    A6 --> FIND
    A7 --> FIND
    A8 --> FIND
    A9 --> FIND
```

Each policy has its own scope, evidence requirements, assessment rules and standards references.

Findings retain traceability to the evidence and rules that produced them.

## 5. Risk and Modernization

Assessment findings provide inputs to organizational risk analysis and modernization planning.

```mermaid
flowchart LR
    F[Assessment Findings]
    O[Organizational Context]

    F --> R[Risk Assessment]
    O --> R

    R --> P[Prioritization]
    P --> M[Modernization Plans]
    M --> V[Migration Validation]
    V --> RA[Reassessment]
    RA --> F
```

PQC migration is a major use case, but the framework is designed to support cryptographic modernization beyond the initial migration.

## 6. Architectural Boundaries

The framework follows separation of concerns and dependency inversion.

- **Domain:** Defines assets, evidence, relationships and assessment concepts.
- **Collection:** Discovers assets and obtains evidence.
- **Runtime:** Identifies collection environment and capabilities.
- **Inventory:** Manages assets and their relationships.
- **BOM:** Provides CycloneDX interoperability.
- **Assessment:** Evaluates evidence against versioned requirements.
- **Standards:** Maintains authoritative publications and provisions.
- **Risk:** Evaluates technical findings against organizational context.
- **Modernization:** Coordinates cryptographic replacement activities.
- **Application:** Coordinates workflows.
- **Infrastructure:** Implements persistence and external integrations.

The domain remains independent of OpenSSL, CycloneDX, databases and CLI implementations.

## 7. Development Roadmap

| Phase | Focus |
|---|---|
| 1 | Domain and evidence foundations |
| 2 | Runtime and collection architecture |
| 3 | TLS and certificate assessment |
| 4 | Cryptographic inventory and CBOM |
| 5 | Standards and policy management |
| 6 | Broader cryptographic discovery |
| 7 | Risk and PQC modernization |
| 8 | Continuous cryptographic assurance |

The architecture describes the intended system. Implementation will progress incrementally, with completed and planned capabilities documented separately.

## 8. Further Documentation

| Subject | Documentation |
|---|---|
| Domain design | `domain/` |
| Package organization | `package-architecture.md` |
| Collection requirements | `collection/` |
| CycloneDX integration | `interoperability/cyclonedx-cbom.md` |
| Assessment methodology | `../../assessment/assessment-methodology.md` |
| Assessment policies | `../../policies/` |
| Standards references | `../../standards/standards-reference.md` |
| Continuous assurance | `modernization/continuous-assurance.md` |

**Guiding principle:** Discover cryptographic assets, preserve reliable evidence, assess evolving requirements and support continuous modernization.
