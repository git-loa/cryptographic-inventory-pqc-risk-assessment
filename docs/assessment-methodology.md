# Assessment Methodology

## 1. Purpose

This document defines the rules used to assess collected TLS evidence and identify potential post-quantum cryptography (PQC) migration concerns.

The assessment uses explicit classifications rather than an aggregate risk score. Results reflect the implemented rules and available evidence; they do not constitute a complete security audit.

## 2. Classification Labels

| Classification           | Meaning                                                      |
| ------------------------ | ------------------------------------------------------------ |
| `acceptable`             | Meets the project's current rule for the assessed dimension. |
| `acceptable_with_review` | Requires further security review or migration consideration. |
| `unacceptable`           | Explicitly excluded by the current policy.                   |
| `unknown`                | Evidence is missing, unrecognized, or not covered by a rule. |

These classifications are project-specific, not universal security ratings.

## 3. Assessment Framework

The framework defines eight assessment areas:

| Policy | Scope                          | Status                                                                       |
| ------ | ------------------------------ | ---------------------------------------------------------------------------- |
| A1     | TLS configuration quality      | Implemented                                                                  |
| A2     | Key-establishment exposure     | Evidence collection available; separate assessment policy not yet integrated |
| A3     | Authentication exposure        | Not implemented                                                              |
| A4     | Evidence quality and coverage  | Not implemented as a separate policy                                         |
| A5     | Contextual risk                | Not implemented                                                              |
| A6     | Migration feasibility          | Not implemented                                                              |
| A7     | Mitigations and residual risk  | Not implemented                                                              |
| A8     | Recommendations and governance | Not implemented                                                              |

Only A1 is currently registered in the default assessment registry.

## 4. A1 — TLS Configuration Quality

A1 evaluates four dimensions independently.

| Rule | Dimension                        | Classification summary                                                                                                                                                                            |
| ---- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A1.1 | TLS version                      | TLS 1.3: `acceptable`; TLS 1.2: `acceptable_with_review`; deprecated versions: `unacceptable`; otherwise: `unknown`.                                                                              |
| A1.2 | Cipher suite                     | Recognized TLS 1.3 AEAD suites and listed TLS 1.2 ECDHE AEAD suites: `acceptable`; selected suites require review; excluded or unrecognized suites follow explicit rules.                         |
| A1.3 | Certificate public-key algorithm | ML-DSA: `acceptable`; RSA, EC, Ed25519, and Ed448: `acceptable_with_review`; DSA: `unacceptable`; otherwise: `unknown`.                                                                           |
| A1.4 | Certificate signature algorithm  | Recognized ML-DSA signatures: `acceptable`; recognized classical signatures: generally `acceptable_with_review`; SHA-1 signatures: `unacceptable`; unsupported or incomplete evidence: `unknown`. |

The cipher-suite and signature rules use explicit allowlists and recognized algorithm identifiers. Unlisted values are not automatically classified as secure or insecure.

**Important limitations:**

* TLS version alone does not establish the security of the complete configuration.
* Cipher-suite classification depends on the negotiated TLS version and recognized suite names.
* Certificate public-key classification does not validate certificate trust, hostname validity, or end-to-end deployment support.
* RSA-PSS assessment does not fully validate all signature parameters.
* A certificate's public-key algorithm and its signature algorithm represent different properties.

A1 produces four structured findings. It does not calculate an overall PQC risk score.

## 5. Key-Establishment Evidence

The collection module obtains key-establishment group information through a separate OpenSSL handshake.

This evidence describes the separate probe's observed negotiation. It does not establish every mechanism supported by the server or guarantee that the main scan negotiated the same group.

Unavailable or unrecognized evidence must remain explicit rather than being interpreted as proof of security or insecurity.

## 6. References

* RFC 9325 — Recommendations for Secure Use of TLS and DTLS.
* RFC 9881 — Use of ML-DSA in X.509 Public Key Infrastructure.

These references inform the assessment, but the implemented project rules may be narrower than the standards.
