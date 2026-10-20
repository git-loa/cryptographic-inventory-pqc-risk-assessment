# System Architecture

## 1. Purpose

The Cryptographic Inventory and PQC Risk Assessment project collects TLS cryptographic evidence and evaluates it against documented assessment policies.

The architecture separates five responsibilities:

* **Collection:** Observe TLS configurations and certificate properties.
* **Assessment:** Apply documented rules to collected evidence.
* **Storage:** Persist evidence and assessment results.
* **Application:** Coordinate scanning, assessment, and reporting.
* **Reporting:** Present findings, supporting evidence, and limitations.

This separation supports independent testing, explainable assessments, and reassessment without unnecessary network rescanning.

> **Status:** This document describes the target architecture. The existing repository will be migrated incrementally.

## 2. System Architecture

```mermaid
flowchart TB
    User([User])

    subgraph CLI["Command-Line Interface"]
        Entry["pipeline.py"]
        Commands["cli.py"]
    end

    subgraph App["Application Services"]
        ScanService["Scan Service"]
        AssessService["Assessment Service"]
        ReportService["Report Service"]
    end

    subgraph Scanner["Evidence Collection"]
        TLS["TLS Scanner"]
        Cert["Certificate Parser"]
        KE["Key Establishment Observer"]
    end

    subgraph Engine["Assessment Engine"]
        Orchestrator["Policy Orchestrator"]
        Registry["Policy Registry"]
        A1["A1: TLS Configuration"]
        A2["A2: Key Establishment"]
    end

    subgraph Storage["Persistence"]
        Repository[("JSON Repository")]
    end

    subgraph Reporting["Report Generation"]
        Renderer["Markdown Renderer"]
        Output["Markdown Report"]
    end

    User --> Entry
    Entry --> Commands

    Commands --> ScanService
    Commands --> AssessService
    Commands --> ReportService

    ScanService --> TLS
    ScanService --> Cert
    ScanService --> KE
    ScanService --> Repository

    AssessService --> Repository
    AssessService --> Orchestrator

    Orchestrator --> Registry
    Registry --> A1
    Registry --> A2
    Orchestrator --> Repository

    ReportService --> Repository
    ReportService --> Renderer
    Renderer --> Output

    classDef policy fill:#e8f2ff,stroke:#3973ac,color:#111
    class A1,A2 policy
```

### Component responsibilities

| Component               | Responsibility                                   |
| ----------------------- | ------------------------------------------------ |
| `pipeline.py`           | Application entry point and command dispatch     |
| `cli.py`                | Command-line arguments and terminal presentation |
| `scan_service.py`       | Coordinates evidence collection                  |
| `assessment_service.py` | Coordinates policy execution                     |
| `report_service.py`     | Coordinates report generation                    |
| `tls_scanner.py`        | Collects TLS endpoint observations               |
| `certificate_parser.py` | Extracts certificate properties                  |
| `key_establishment.py`  | Collects key-establishment observations          |
| `interfaces.py`         | Defines the assessment policy contract           |
| `registry.py`           | Maintains available assessment policies          |
| `orchestrator.py`       | Coordinates policy execution                     |
| `json_repository.py`    | Loads and persists structured data               |
| `markdown.py`           | Renders assessment results into Markdown         |

The CLI must not contain scanning algorithms or assessment rules. The report renderer must not make independent security decisions.

## 3. Data Flow

```mermaid
flowchart TD
    A["Target Domains"] --> B["Evidence Collection"]
    B --> C["Normalized Scan Evidence"]
    C --> D[("Persisted Evidence")]

    D --> E["Assessment Service"]
    E --> F["Assessment Orchestrator"]

    F --> G["A1: TLS Configuration"]
    F --> H["A2: Key Establishment"]

    G --> I["Policy Results"]
    H --> I

    I --> J[("Persisted Assessment Run")]
    J --> K["Report Service"]
    K --> L["Markdown Report"]

    D -. "Reassess saved evidence" .-> E
    J -. "Regenerate report" .-> K
```

The workflow has three independently executable operations:

1. **Scan:** Collect and persist evidence.
2. **Assess:** Apply policies to available evidence and persist results.
3. **Report:** Render saved assessment results.

This design allows users to reassess evidence after policy changes without automatically repeating network scans.

If new rules require evidence that was never collected, the assessment must report that limitation.

## 4. Assessment Policy Architecture

Assessment policies implement a shared contract and produce standardized results.

```mermaid
flowchart TB
    Evidence["Collected Evidence"]
    Context["Assessment Context"]
    Orchestrator["Assessment Orchestrator"]

    subgraph Policies["Registered Policies"]
        A1["A1: TLS Configuration"]
        A2["A2: Key Establishment"]
        Future["A3–A8: Future Policies"]
    end

    subgraph Results["Standardized Policy Results"]
        Status["Execution Status"]
        Findings["Assessment Findings"]
        Rationale["Rules and Rationale"]
    end

    Evidence --> Context
    Context --> Orchestrator

    Orchestrator --> A1
    Orchestrator --> A2
    Orchestrator --> Future

    A1 --> Status
    A2 --> Status
    Future --> Status

    A1 --> Findings
    A2 --> Findings
    Future --> Findings

    Findings --> Rationale
```

Each policy is responsible for evaluating its defined assessment dimensions.

The orchestrator is responsible for invoking policies and collecting results. It should not duplicate the internal rules of individual policies.

### Policy contract

The proposed interface is:

```python
from typing import Protocol


class AssessmentPolicy(Protocol):
    @property
    def policy_id(self) -> str:
        ...

    @property
    def policy_version(self) -> str:
        ...

    def assess(self, context: "AssessmentContext") -> "PolicyResult":
        ...
```

`AssessmentContext` provides the evidence and applicable configuration.

`PolicyResult` contains the execution status, findings, and limitations.

This interface is a design proposal; it has not yet been established as the repository's implemented contract.

## 5. Assessment Status and Classification

Policy execution status and finding classification are independent concepts.

```mermaid
flowchart TD
    Start["Execute Assessment Policy"]

    Start --> Execution{"Execution outcome"}

    Execution -->|Completed| Complete["completed"]
    Execution -->|Incomplete| Partial["partial"]
    Execution -->|Not executed| NotRun["not_assessed"]
    Execution -->|Error| Failed["failed"]

    Complete --> Evaluate["Evaluate Evidence"]
    Partial --> Limitations["Record Partial Results and Limitations"]

    Evaluate --> Decision{"Supported conclusion?"}

    Decision -->|Rule satisfied| Acceptable["acceptable"]
    Decision -->|Review required| Review["acceptable_with_review"]
    Decision -->|Rule violated| Unacceptable["unacceptable"]
    Decision -->|Insufficient evidence| Unknown["unknown"]

    Limitations --> Unknown
```

**Execution status** describes whether the assessment ran successfully.

**Classification** describes what the evidence supports.

A completed policy may produce an `unknown` finding. A failed policy must not automatically produce an `unacceptable` finding.

The methodology document defines the actual classification criteria.

## 6. Storage and Reporting

The initial persistence implementation will use JSON.

The storage layer will manage:

* Scan evidence.
* Assessment runs.
* Schema validation.
* Supported schema versions.
* Loading and saving results.

The reporting layer will render saved assessment results without repeating assessment logic.

Reports should include:

* Assessment scope and scan coverage.
* Successful scans and failures.
* Findings grouped by policy.
* Classifications and supporting rationale.
* Evidence provenance where available.
* Unknown findings and missing evidence.
* Policy and methodology versions.
* Assessment limitations.

No unexplained aggregate score should replace individual findings.

## 7. Target Repository Structure

```text
cryptographic-inventory-pqc-risk-assessment/
├── config/
│   ├── domains.txt
│   └── assessment.toml
├── docs/
│   ├── architecture.md
│   ├── assessment-methodology.md
│   ├── data-model.md
│   └── decisions/
├── src/
│   ├── pipeline.py
│   ├── cli.py
│   ├── application/
│   │   ├── scan_service.py
│   │   ├── assessment_service.py
│   │   └── report_service.py
│   ├── scanner/
│   │   ├── tls_scanner.py
│   │   ├── certificate_parser.py
│   │   └── key_establishment.py
│   ├── assessment/
│   │   ├── models.py
│   │   ├── interfaces.py
│   │   ├── registry.py
│   │   ├── orchestrator.py
│   │   └── policies/
│   │       ├── a1_tls_configuration.py
│   │       ├── a2_key_establishment.py
│   │       └── ...
│   ├── storage/
│   │   └── json_repository.py
│   ├── reporting/
│   │   ├── markdown.py
│   │   └── templates/
│   └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   └── fuzz/
├── reports/
├── data/
├── pyproject.toml
└── README.md
```

This is the target structure, not a claim that all these paths already exist.

## 8. Migration Plan

Implementation will proceed incrementally:

1. Finalize the architecture and data-model contracts.
2. Introduce shared assessment models and the policy interface.
3. Migrate A1 and its tests.
4. Define and integrate A2.
5. Standardize evidence and assessment persistence.
6. Align reporting with the shared result model.
7. Replace the legacy CLI workflow.
8. Remove obsolete scoring code and update documentation.
9. Introduce additional policies when their methodologies and evidence requirements are defined.

Each phase should be independently testable.

Moving files alone does not complete the migration. The implementation, data contracts, and tests must agree with the architecture.
