# TLS Inventory Scanner & PQC Risk Assessment

A Python project for collecting TLS configuration and certificate metadata, then assessing selected cryptographic properties relevant to post-quantum migration. It produces structured JSON data and a Markdown report.

The project is under active development. Its current assessment rules are deliberately scoped and should not be treated as a complete security audit or a production-ready PQC readiness determination.

## Current status

- **TLS inventory:** Scans configured domains and collects negotiated TLS details.
- **Certificate metadata:** Extracts X.509 identity, validity, public-key, signature, SAN, and usage fields.
- **A1 — TLS configuration quality:** Four rule-based findings are produced from each TLS scan and included in combined JSON and Markdown reports.
- **A2 — Key-establishment exposure:** Evidence collection and assessment are included in combined reports, but the recognized mechanism registry remains limited.
- **Integration:** The legacy numerical PQC heuristic is still emitted for backward compatibility; it is not a standards-based or complete risk measure. A1 findings are separate and are not collapsed into an arbitrary aggregate score. A3–A8 are not implemented as complete assessment stages.

See [Assessment Methodology](docs/assessment-methodology.md) for the current rules, limitations, and implementation status.

## Project layout

```text
config/                 Domain input
docs/                   Assessment methodology
src/
  pipeline.py           CLI pipeline orchestration
  run_scan.py           TLS scanning entry point
  scanner/
    tls_scanner.py      TLS inventory collection
    certificate_parser.py
    key_establishment.py
    pqc_assessment.py   A2 key-establishment assessment
    pqc_scoring.py      A1 classifiers and legacy scoring
    a1_assessment.py    Structured A1 assessment
    assessment.py       Assessment orchestration
    json_io.py          JSON input/output
    combined_report.py  Combined JSON report
    markdown_report.py  Markdown report generation
tests/                  Unit and fuzz tests
templates/              Report template
```

## Run

Install the project's dependencies in your Python environment, then view the available options:

```powershell
python -m src.pipeline --help
```

Run the full existing pipeline against the configured domain list:

```powershell
python -m src.pipeline --all --domains config/domains.txt
```

The current pipeline writes:

```text
data/processed/tls_results.json
data/processed/pqc_scores.json
reports/combined_report.json
reports/tls_pqc_report.md
```

The output named `pqc_scores.json` currently contains results from the legacy heuristic. Do not interpret its numerical score as a standards-based or fully validated PQC risk measure.

## Development and testing

Run the test suite from the repository root:

```powershell
pytest
```

The tests validate implemented behavior and data flow; they do not constitute a complete security audit.

## Planned work

1. Complete A2 mechanism classification, evidence validation, and tests.
2. Strengthen report-schema validation and verify the integrated A1/A2 output end to end.
3. Define any overall assessment policy explicitly, without arbitrary score weights.
4. Retire the legacy heuristic only after the replacement assessment is tested; then implement A3–A8 incrementally.
