# TLS Inventory Scanner & PQC Risk Assessment

A Python project for collecting TLS configuration and certificate metadata, then assessing selected cryptographic properties relevant to post-quantum migration. It produces structured JSON data and a Markdown report.

The project is under active development. Its current assessment rules are deliberately scoped and should not be treated as a complete security audit or a production-ready PQC readiness determination.

## Current status

- **TLS inventory:** Scans configured domains and collects negotiated TLS details.
- **Certificate metadata:** Extracts X.509 identity, validity, public-key, signature, SAN, and usage fields.
- **A1 — TLS configuration quality:** Rule-based classifiers exist for TLS version, cipher suite, certificate public-key algorithm, and certificate signature algorithm.
- **A2 — Key-establishment exposure:** Collects negotiated-group evidence through a separate OpenSSL handshake and recognizes a limited set of classical groups.
- **Integration:** The existing CLI pipeline still uses the legacy numerical PQC heuristic. The A1 classifiers are not yet integrated into a replacement assessment pipeline; A3–A8 are not implemented as complete assessment stages.

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

1. Integrate the A1 rule-based findings and A2 evidence assessment into the canonical pipeline.
2. Define and test explicit assessment aggregation without arbitrary score weights.
3. Implement and document A3–A8 incrementally.
4. Replace the legacy heuristic and update report schemas once the replacement is tested.
