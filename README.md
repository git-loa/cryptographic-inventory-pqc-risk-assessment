
# TLS Inventory Scanner & PQC Risk Assessment

A lightweight Python project for analyzing the cryptographic posture of TLS‑enabled domains
and generating a combined TLS + PQC report. The pipeline scans domains, scores post‑quantum
readiness, merges results, and produces a Markdown summary using a Jinja2 template.

Built for learning, experimentation, and practical problem‑solving in applied cryptography
and early post‑quantum security.

---

## Project Structure

```
.
├── config/                     # Domain lists and configuration files
├── data/
│   ├── raw/                    # Raw scan outputs
│   └── processed/              # Normalized TLS + PQC JSON data
├── logs/                       # Runtime logs
├── reports/                    # Combined JSON + Markdown reports
├── src/
│   ├── run_scan.py             # TLS scanning entrypoint
│   ├── scanner/
│   │   ├── score_pqc_from_json.py   # PQC scoring module
│   │   ├── combined_report.py        # Merge TLS + PQC results
│   │   ├── markdown_report.py        # Markdown generator
│   │   ├── json_io.py                # Load/save TLS + PQC JSON
│   │   ├── domain_loader.py          # Domain list loader
│   │   ├── print_tls_results.py      # CLI printing utilities
│   │   ├── tls_scanner.py            # TLS scanning engine
│   │   ├── models.py                 # TypedDict models
│   │   ├── utils/                    # Helpers, logger, parsing utilities
│   │   └── testing/                  # Internal testing helpers
├── templates/                  # Jinja2 Markdown template
├── tests/                      # Unit tests + fuzz tests
└── pipeline.py                 # Unified pipeline orchestrator
```

---

## Development Notes

This project is built for:

- clear, readable code
- small, testable components
- deterministic pipeline behavior
- early exploration of PQC‑related risk modeling
- practical cryptographic engineering learning

It is not intended as a production‑grade scanner.

---

## Usage

View all available commands:

```
python -m src.pipeline --help
```

Which displays:

```
usage: pipeline.py [-h] [--runscanner] [--scorepqc] [--combined] [--markdown]
                   [--author AUTHOR] [--organization ORGANIZATION] [--all]
                   [--print-tls-results] [-s] [-v] [--domains DOMAINS] [--debug]

TLS + PQC Pipeline Runner

options:
  -h, --help            show this help message and exit
  --runscanner          Run TLS scanner
  --scorepqc            Run PQC scoring
  --combined            Generate combined TLS+PQC JSON
  --markdown            Generate Markdown report
  --author AUTHOR       Name of the report author
  --organization ORGANIZATION
                        Organization or affiliation
  --all                 Run all stages in order
  --print-tls-results   Print saved TLS results
  -s, --summary         Print summary table
  -v, --verbose         Print detailed results
  --domains DOMAINS     Path to domains file
  --debug               Enable debug logging
```

### Examples

```
python -m src.pipeline --all --domains config/domains.txt
python -m src.pipeline --markdown --author "Leonard Afeke"
```

---

## Output Files

The pipeline writes fixed, predictable files:

```
data/processed/tls_results.json
data/processed/pqc_scores.json
reports/combined_report.json
reports/tls_pqc_report.md
```

---

## Purpose

This project explores:

- TLS cryptographic inventory
- simple PQC‑related scoring ideas
- reproducible pipeline design
- clear reporting using Jinja2
- early cryptographic engineering and automation practice

It is not intended as a production‑grade scanner.

---

## Future Improvements

- Per‑domain Markdown reports
- Optional timestamped output for historical tracking
- Certificate Transparency (CT) log integration
- OCSP/CRL certificate health checks
- Expanded PQC scoring heuristics
- Parallel domain scanning
- HTML report generation
- Rust‑based PQC modules for performance comparison
- Configurable output paths and templates
