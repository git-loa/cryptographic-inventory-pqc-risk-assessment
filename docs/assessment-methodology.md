# Assessment Methodology

## 1. Purpose

This document describes the project's rule-based assessment of TLS configuration and post-quantum cryptography (PQC) exposure. Findings are based on evidence collected by the scanner and must not be treated as a complete security audit or proof that a system is—or is not—post-quantum secure.

The assessment uses explicit rules rather than an unexplained aggregate score. A result of `unknown` means the available evidence or current rules do not support a classification; it does not mean `unacceptable`.

## 2. Classification labels

| Label | Meaning |
|---|---|
| `acceptable` | Meets the project's current rule for this specific dimension. |
| `acceptable_with_review` | Recognized, but requires additional review or migration consideration. |
| `unacceptable` | Explicitly excluded by the current project policy. |
| `unknown` | Evidence is missing, unrecognized, inconsistent, or not covered by a rule. |

These are project-policy labels, not universal security ratings. A result in one dimension does not determine the result of another.

## 3. Assessment framework and implementation status

| Area | Scope | Current status |
|---|---|---|
| **A1 — TLS configuration quality** | Negotiated TLS version, cipher suite, certificate public-key algorithm, and certificate signature algorithm. | Implemented and integrated as four structured findings in combined JSON and Markdown reports; see Section 4. |
| **A2 — Key-establishment exposure** | Observed TLS key-establishment group and the quality of its evidence. | Partial: collection and classical-group recognition exist; unrecognized groups remain unknown. |
| **A3 — Authentication exposure** | Assessment of authentication mechanisms in the context of quantum threats. | Not yet integrated as a separate assessment. |
| **A4 — Evidence quality and coverage** | Completeness and reliability of evidence supporting findings. | Partially handled by A2 validation; no framework-wide assessment yet. |
| **A5 — Contextual risk** | Business context, data sensitivity, and consequences of exposure. | Not implemented. |
| **A6 — Migration feasibility** | Practical constraints and dependencies affecting migration. | Not implemented. |
| **A7 — Mitigations and residual risk** | Existing mitigations and risk remaining after their consideration. | Not implemented. |
| **A8 — Recommendations and governance** | Actionable remediation and migration guidance. | Not implemented as a framework-wide assessment. |

The status describes the current code, not the intended end state. A1 and A2 findings remain separate; the legacy numerical heuristic is still emitted for compatibility and is not a framework-wide risk assessment.

## 4. A1 — TLS configuration quality

A1 evaluates four separate evidence dimensions. Its findings are included in each combined assessment report under `a1`. It does not estimate an overall PQC risk score.

### A1.1 — Negotiated TLS version

| Observed value | Classification |
|---|---|
| TLS 1.3 | `acceptable` |
| TLS 1.2 | `acceptable_with_review` |
| TLS 1.1, TLS 1.0, SSL 2, SSL 3 | `unacceptable` |
| Missing or unrecognized | `unknown` |

TLS 1.2 is flagged for review as a project policy choice; the version alone does not establish whether its configuration is secure.

### A1.2 — Cipher suite

The classifier uses the negotiated version and explicit suite rules.

- **TLS 1.3:** AES-GCM, ChaCha20-Poly1305, and AES-128-CCM are recognized as `acceptable`; AES-128-CCM-8 is `acceptable_with_review`.
- **TLS 1.2:** Listed ECDHE AEAD suites are `acceptable`; listed static RSA key-transport and ECDHE CBC suites are `acceptable_with_review`.
- **Excluded suites:** Names matching the current NULL, RC4, export-grade, or 3DES rules are `unacceptable`.
- **Missing or unrecognized evidence:** `unknown`.

The allowlists are intentionally explicit and are not an exhaustive parser for every cipher-suite name. In particular, the scanner does not currently establish whether the TLS 1.2 `encrypt_then_mac` extension was negotiated, so CBC findings retain their review status. The presence of RSA in an ECDHE-RSA suite refers to authentication, not static RSA key transport.

### A1.3 — Certificate public-key algorithm

| Algorithm | Classification |
|---|---|
| ML-DSA | `acceptable` |
| RSA, EC, Ed25519, Ed448 | `acceptable_with_review` |
| DSA | `unacceptable` |
| Missing or unrecognized | `unknown` |

The parser preserves the ML-DSA parameter set (ML-DSA-44, ML-DSA-65, or ML-DSA-87) and public-key algorithm OID. The classification is algorithm-level; it does not validate certificate trust, chain construction, hostname validity, key strength, or end-to-end deployment support.

### A1.4 — Certificate signature algorithm

| Algorithm or evidence | Classification |
|---|---|
| RSA with SHA-256/384/512; ECDSA with SHA-256/384/512; Ed25519; Ed448 | `acceptable_with_review` |
| RSA or ECDSA with SHA-1 | `unacceptable` |
| RSA-PSS with recognized SHA-256/384/512 hash metadata | `acceptable_with_review` |
| ML-DSA-44/65/87 signature OID | `acceptable` |
| Missing or unrecognized OID; RSA-PSS without recognized hash metadata | `unknown` |

A1.4 concerns the signature on the certificate, not the signature scheme negotiated for a TLS handshake. RSA-PSS parameter validation is incomplete; a recognized hash alone does not prove that all parameters are compliant. An ML-DSA classification does not validate the certificate chain or prove end-to-end support.

The certificate's subject public-key algorithm (A1.3) and its issuer's certificate signature algorithm (A1.4) are separate fields and are assessed independently.

## 5. A2 — Key-establishment exposure

A2 uses observed key-establishment group evidence collected through a separate OpenSSL handshake. The current registry explicitly recognizes `X25519` and `secp256r1` as classical groups. Other identifiers remain `unknown` until the project verifies and adds a classification rule.

The assessment validates scan status and evidence status, and does not infer post-quantum key establishment from TLS version, cipher suite, or certificate public-key algorithm. Because the group is collected in a separate connection, it is evidence of that probe's negotiation—not proof of every mechanism the server supports or of the exact negotiation seen by the main scan.

## 6. Evidence and limitations

- Certificate parsing extracts metadata; it does not establish certificate trust or hostname validity.
- A negotiated group, certificate key, certificate signature, and cipher suite describe different aspects of a TLS connection and must not be conflated.
- Unknown or unavailable evidence should remain explicit in reports rather than being treated as a positive or negative finding.
- Current rules are intentionally limited to the values implemented and tested in the repository.
- No framework-wide risk aggregation or migration-priority score is currently defined.

## 7. References

- RFC 9325 — Recommendations for Secure Use of TLS and DTLS.
- RFC 9881 — Use of ML-DSA in X.509 Public Key Infrastructure.

These references inform parts of the policy; the tables above describe the project's implemented rules, which may be narrower than the standards.
