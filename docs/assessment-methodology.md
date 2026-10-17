# Assessment Methodology

## 1. Purpose and scope

This document records the initial policy used by the TLS Inventory Scanner & PQC Risk Assessment project to classify selected TLS configuration evidence.

The current A1 assessment evaluates four dimensions over time:

- **A1.1 — TLS version**
- **A1.2 — Cipher suite**
- A1.3 — Certificate public-key algorithm
- A1.4 — Certificate signature algorithm

This document currently defines A1.1 and A1.2. The classifications are rule-based findings about observed configuration evidence. They are not, by themselves, a complete security audit, a proof of exploitability, or a determination that a system is post-quantum secure.

The project uses the following classification labels:

| Classification | Meaning |
|---|---|
| `acceptable` | The observed value matches a suite or protocol covered by the project's current acceptable baseline. |
| `acceptable_with_review` | The value is recognized, but a security consideration or missing contextual evidence warrants review. |
| `unacceptable` | The observed value matches a category explicitly excluded by the project's current baseline. |
| `unknown` | Evidence is missing, unrecognized, or outside the implemented rules; the assessment does not make a supported classification. |

These labels describe the project's assessment policy. They should not be interpreted as universal guarantees of security or insecurity.

## 2. A1.1 — TLS version assessment

The implementation classifies the negotiated TLS version as follows:

| Observed version | Classification | Rationale |
|---|---|---|
| `TLSv1.3` | `acceptable` | Preferred modern TLS version under the project's baseline. |
| `TLSv1.2` | `acceptable_with_review` | TLS 1.2 can be securely configured, but the rest of the TLS configuration should be reviewed. |
| `TLSv1.1` | `unacceptable` | Deprecated protocol version excluded from the project's baseline. |
| `TLSv1.0` | `unacceptable` | Deprecated protocol version excluded from the project's baseline. |
| `SSLv2` or `SSLv3` | `unacceptable` | Obsolete protocol versions excluded from the project's baseline. |
| Missing or unrecognized value | `unknown` | The implementation does not have sufficient recognized evidence to classify the version. |

### Interpretation

The `acceptable_with_review` result for TLS 1.2 is a **project policy choice**, not a claim that TLS 1.2 is inherently insecure or necessarily less safe than TLS 1.3. RFC 9325 gives configuration recommendations for TLS 1.2 as well as TLS 1.3. A version-only finding cannot establish whether the full TLS 1.2 configuration follows those recommendations.

The implementation currently recognizes the exact version strings listed in the table. Values not covered by these rules return `unknown`.

## 3. A1.2 — Cipher-suite assessment

Cipher-suite classification depends on both the observed cipher-suite name and the negotiated TLS version. The implementation uses explicit allowlists rather than assuming every unrecognized suite is either secure or insecure.

### 3.1 TLS 1.3

| Observed cipher suite | Classification | Rationale |
|---|---|---|
| `TLS_AES_128_GCM_SHA256` | `acceptable` | Recognized AEAD suite in the project's baseline. |
| `TLS_AES_256_GCM_SHA384` | `acceptable` | Recognized AEAD suite in the project's baseline. |
| `TLS_CHACHA20_POLY1305_SHA256` | `acceptable` | Recognized AEAD suite in the project's baseline. |
| `TLS_AES_128_CCM_SHA256` | `acceptable` | Recognized AEAD suite in the project's baseline. |
| `TLS_AES_128_CCM_8_SHA256` | `acceptable_with_review` | Uses a truncated authentication tag and receives additional review under the project's policy. |
| Other or unrecognized suite | `unknown` | Not covered by the current TLS 1.3 allowlist. |

The suite allowlist is an implementation policy, not an exhaustive list of every suite defined by the TLS standards. A result of `unknown` means the current classifier has no rule for the observed value; it does not, by itself, prove that the suite is insecure.

### 3.2 TLS 1.2

The implementation currently recognizes three groups:

| Suite group | Classification | Rationale |
|---|---|---|
| Explicitly listed ECDHE AEAD suites, including AES-GCM and ChaCha20-Poly1305 | `acceptable` | The listed suites combine ephemeral key agreement with authenticated encryption. |
| Explicitly listed static RSA key-transport suites | `acceptable_with_review` | Static RSA key transport does not provide forward secrecy. |
| Explicitly listed ECDHE CBC suites | `acceptable_with_review` | CBC-based TLS 1.2 suites require additional review against current TLS guidance and relevant negotiated extensions. |
| Other or unrecognized suite | `unknown` | Not covered by the current TLS 1.2 allowlists. |

The recognized TLS 1.2 ECDHE AEAD list includes the four AES-GCM suites recommended by RFC 9325:

- `TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`
- `TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384`
- `TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256`
- `TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384`

The implementation also recognizes corresponding OpenSSL-style names and listed ECDHE ChaCha20-Poly1305 suites. The precise supported names are defined in `src/scanner/pqc_scoring.py`; this document describes the policy categories rather than replacing the code's allowlists.

### 3.3 Static RSA key transport

Static RSA suites receive `acceptable_with_review`, not `acceptable`, because static RSA key transport lacks forward secrecy. RFC 9325 says implementations **SHOULD NOT** negotiate static RSA cipher suites. The project's label signals that the suite is recognized but has a security limitation requiring attention.

This rule concerns the key-transport mechanism. The presence of the string `RSA` in an ECDHE-RSA suite does not mean that the suite uses static RSA key transport: ECDHE provides the ephemeral key agreement, while RSA is used for authentication.

### 3.4 CBC-based suites

The recognized ECDHE CBC suites receive `acceptable_with_review`. RFC 9325 advises against CBC-based TLS 1.2 cipher suites unless the `encrypt_then_mac` extension has been successfully negotiated.

The current classifier uses the cipher-suite name and TLS version. It does not establish whether `encrypt_then_mac` was negotiated. Therefore, it cannot use that extension as evidence to clear the review finding. This is a limitation of the current evidence model, not a claim that every CBC connection is exploitable.

### 3.5 CCM_8

The TLS 1.3 suite `TLS_AES_128_CCM_8_SHA256` receives `acceptable_with_review` because it uses a truncated authentication tag. The label is a conservative project policy that highlights this difference for review; it should not be read as a claim that the suite is automatically broken.

### 3.6 Unacceptable cipher-suite categories

The current implementation classifies suites as `unacceptable` when their names contain markers for NULL encryption, RC4, export-grade cryptography, or 3DES (including recognized naming variants).

This is the project's explicit exclusion policy. RFC 9325 prohibits NULL encryption and RC4 and disallows suites with insufficient security strength, including export-grade suites. The project's implementation also explicitly excludes 3DES. The name-based checks are a practical classifier, not a general-purpose parser for every possible cipher-suite naming convention.

### 3.7 Missing, unknown, or inconsistent evidence

The classifier returns `unknown` when:

- the cipher-suite name is missing or blank;
- the TLS version is missing or blank;
- the suite is not covered by the allowlist for the observed version; or
- the suite name is associated with a different TLS version than the one observed.

The classifier does not infer security properties for values outside its rules. In particular, `unknown` is not interchangeable with `unacceptable`.

## 4. Standards and references

The policy is informed by the following standards:

1. **RFC 9325 — Recommendations for Secure Use of Transport Layer Security (TLS) and Datagram Transport Layer Security (DTLS):** https://www.rfc-editor.org/rfc/rfc9325.html
   - Provides current guidance on TLS configuration, cipher suites, static RSA key transport, and CBC-based suites.
2. **RFC 8446 — The Transport Layer Security (TLS) Protocol Version 1.3:** https://www.rfc-editor.org/rfc/rfc8446.html
   - Defines TLS 1.3 and its cipher-suite model.
3. **IANA TLS Parameters:** https://www.iana.org/assignments/tls-parameters
   - Registry of TLS-related parameters, including cipher-suite identifiers.

Standards language such as **MUST**, **MUST NOT**, **SHOULD**, and **SHOULD NOT** retains its meaning in the referenced RFCs. The project's four classification labels are its own reporting model and are not labels defined by those RFCs.

## 5. Limitations and future work

- A1.1 and A1.2 are individual dimensions; neither is a complete TLS security assessment.
- A1.2 relies on explicit name allowlists and does not yet classify every standardized cipher suite.
- The current A1.2 evidence does not include whether `encrypt_then_mac` was negotiated.
- A TLS cipher-suite classification alone does not establish post-quantum readiness. Key-establishment exposure and certificate authentication are assessed separately.
- The existing numeric PQC heuristic is separate from these A1 classification results and should not be treated as equivalent to this rule-based methodology.
- The policy and allowlists should be reviewed when standards, implementation evidence, or project scope changes.
