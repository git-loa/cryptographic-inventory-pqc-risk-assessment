# Security Policy

This project is a learning and experimentation tool for TLS cryptographic
inventory and early PQC risk modeling. It is **not** intended for production use
or deployment in security‑critical environments.

---

## Reporting Security Issues

If you discover a security issue in the codebase:

1. Open an issue describing the problem at a high level
2. Do not include sensitive data, private keys, or real‑world credentials
3. Provide steps to reproduce the issue if possible

Since this project is not used in production, issues will be addressed on a
best‑effort basis.

---

## Scope and Limitations

This project:

- does **not** perform active exploitation
- does **not** attempt to bypass security controls
- does **not** guarantee complete or accurate TLS/PQC assessments
- does **not** store or transmit sensitive data
- does **not** provide real‑time security monitoring

All scanning is performed using standard Python libraries and publicly available
TLS metadata.

---

## Responsible Use

When running the scanner:

- Only scan domains you own or have permission to analyze
- Do not use this tool for unauthorized security testing
- Respect rate limits and avoid sending excessive requests

This project is intended for educational exploration of cryptographic posture,
not offensive security.

---

## Dependencies

The project relies on common Python packages.
Keep dependencies updated and review changelogs for security patches.

---

## Future Security Improvements

- Optional domain permission verification
- Safer handling of malformed TLS endpoints
- Additional validation for JSON input/output
- More robust error handling in pipeline stages
