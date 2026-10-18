# Assessment Methodology

## 1. Purpose and scope

This document records the initial policy used by the TLS Inventory Scanner & PQC Risk Assessment project to classify selected TLS configuration evidence.

The current A1 assessment evaluates four dimensions over time:

- **A1.1 — TLS version**
- **A1.2 — Cipher suite**
- A1.3 — Certificate public-key algorithm
- A1.4 — Certificate signature algorithm

This document defines A1.1, A1.2, A1.3, and A1.4. The classifications are rule-based findings about observed configuration evidence. They are not, by themselves, a complete security audit, a proof of exploitability, or a determination that a system is post-quantum secure.

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

## 4. A1.3 — Certificate public-key algorithm assessment

A1.3 classifies the public-key algorithm identified in certificate metadata. Its primary purpose is to flag classical public-key algorithms for post-quantum migration review. It does not, by itself, assess key size, elliptic-curve strength, certificate trust, hostname validity, or whether a deployed TLS connection successfully uses post-quantum authentication.

The implementation uses `parse_certificate()` to extract public-key metadata from X.509 certificates and `classify_public_key_algorithm()` to classify the normalized algorithm name.

### Classification policy

| Observed algorithm name    | Classification           | Rationale                                                                              |
| -------------------------- | ------------------------ | -------------------------------------------------------------------------------------- |
| `ML-DSA`                   | `acceptable`             | Recognized by the project as a standardized post-quantum digital-signature algorithm.  |
| `RSA`                      | `acceptable_with_review` | Classical public-key algorithm requiring post-quantum migration review.                |
| `EC`                       | `acceptable_with_review` | Classical elliptic-curve public-key algorithm requiring post-quantum migration review. |
| `Ed25519`                  | `acceptable_with_review` | Classical public-key/signature algorithm requiring post-quantum migration review.      |
| `Ed448`                    | `acceptable_with_review` | Classical public-key/signature algorithm requiring post-quantum migration review.      |
| `DSA`                      | `unacceptable`           | Explicitly excluded from the project's initial acceptable baseline.                    |
| Missing or blank value     | `unknown`                | The public-key algorithm is unavailable.                                               |
| Other or unrecognized name | `unknown`                | No classification rule exists for the observed value.                                  |

### ML-DSA recognition and metadata

The certificate parser explicitly recognizes the three ML-DSA parameter sets:

| Public-key algorithm | Normalized algorithm name | `public_key_variant` | Public-key algorithm OID  |
| -------------------- | ------------------------- | -------------------- | ------------------------- |
| ML-DSA-44            | `ML-DSA`                  | `ML-DSA-44`          | `2.16.840.1.101.3.4.3.17` |
| ML-DSA-65            | `ML-DSA`                  | `ML-DSA-65`          | `2.16.840.1.101.3.4.3.18` |
| ML-DSA-87            | `ML-DSA`                  | `ML-DSA-87`          | `2.16.840.1.101.3.4.3.19` |

The parser normalizes these variants to the common algorithm name `ML-DSA` for classification. It preserves the specific parameter set separately in `public_key_variant` and extracts the public-key algorithm identifier into `public_key_algorithm_oid`.

The parameter-set identifiers and OIDs follow RFC 9881, which specifies the use of ML-DSA public keys in X.509 certificates.

Integration tests exercise certificate generation, DER encoding, certificate parsing, and A1.3 classification for all three variants. These tests verify that the extracted metadata reaches the classifier consistently.

### Interpretation and limitations

* `acceptable_with_review` for RSA, EC, Ed25519, and Ed448 means that the algorithm is classical and should be considered in post-quantum migration planning. It does **not** mean the algorithm is currently broken or that the certificate is otherwise invalid.
* The `acceptable` result for `ML-DSA` is an algorithm-level policy result. It does not prove that the certificate chain, TLS implementation, clients, or deployment support post-quantum certificates end to end.
* The classifier evaluates the normalized algorithm name only. It does not use RSA key size, elliptic curve, certificate usage, or certificate-chain context to refine this classification. Those properties require separate checks.
* The parser preserves the ML-DSA parameter set and public-key algorithm OID, but A1.3 currently assigns the same classification to all three variants.
* The public-key algorithm OID identifies the certificate's subject public key. It is distinct from the certificate's own signature algorithm identifier, which is represented separately in the parsed metadata.
* `DSA` is excluded by the project's initial policy. This is a project classification decision and should not be interpreted as a complete assessment of every possible DSA deployment or parameter set.

## 5. A1.4 — Certificate signature algorithm assessment

A1.4 classifies the signature algorithm identified in an X.509 certificate's signature algorithm field. This is distinct from the subject public-key algorithm assessed by A1.3. For example, a certificate can contain an ML-DSA subject public key while its issuer signs the certificate using a classical algorithm. Assessing both fields helps distinguish the subject's key type from the algorithm used to sign the certificate.

The implementation uses `parse_certificate()` to extract `certificate_signature_algorithm_oid` and `certificate_signature_hash_algorithm`, then passes those values to `classify_certificate_signature()`. The signature OID is the primary input to the classification rules. Hash-algorithm metadata is additionally used for RSA-PSS.

### Classification policy

| Observed certificate signature algorithm | Classification | Rationale |
|---|---|---|
| RSA with SHA-256, SHA-384, or SHA-512 | `acceptable_with_review` | Recognized classical signature algorithm requiring post-quantum migration review. |
| ECDSA with SHA-256, SHA-384, or SHA-512 | `acceptable_with_review` | Recognized classical signature algorithm requiring post-quantum migration review. |
| Ed25519 or Ed448 | `acceptable_with_review` | Recognized classical signature algorithm requiring post-quantum migration review. |
| RSA with SHA-1 | `unacceptable` | SHA-1 certificate signatures are excluded by the project's initial policy. |
| ECDSA with SHA-1 | `unacceptable` | SHA-1 certificate signatures are excluded by the project's initial policy. |
| RSA-PSS with SHA-256, SHA-384, or SHA-512 metadata | `acceptable_with_review` | The hash is recognized, but RSA-PSS remains a classical signature scheme requiring post-quantum migration review. |
| ML-DSA-44, ML-DSA-65, or ML-DSA-87 signature OID | `acceptable` | Recognized standardized post-quantum signature algorithm under the project's current baseline. |
| Missing or blank signature OID | `unknown` | The certificate signature algorithm identifier is unavailable. |
| Unrecognized signature OID | `unknown` | No classification rule exists for the observed identifier. |

The recognized OIDs for the ML-DSA variants are:

| Signature algorithm | Signature algorithm OID |
|---|---|
| ML-DSA-44 | `2.16.840.1.101.3.4.3.17` |
| ML-DSA-65 | `2.16.840.1.101.3.4.3.18` |
| ML-DSA-87 | `2.16.840.1.101.3.4.3.19` |

### Interpretation and limitations

- `acceptable_with_review` for RSA, ECDSA, Ed25519, Ed448, and RSA-PSS indicates that the certificate signature algorithm is recognized but remains a classical signature scheme requiring post-quantum migration review. It does not, by itself, mean the certificate is invalid or currently exploitable.
- The `unacceptable` classification for SHA-1 is an explicit project policy. It reflects the project's exclusion of SHA-1 certificate signatures rather than a complete evaluation of the certificate or its trust chain.
- The `acceptable` classification for an ML-DSA signature OID is an algorithm-level policy result. It does not establish that the certificate chain, relying parties, TLS stack, or deployment support post-quantum signatures end to end.
- RSA-PSS classification uses the signature OID and the hash-algorithm metadata exposed by the parser. When the hash metadata is SHA-256, SHA-384, or SHA-512, the result is `acceptable_with_review`; otherwise, the result is `unknown`. The current classifier does not fully validate all RSA-PSS parameters, including the mask generation function, salt length, or parameter encoding. A recognized hash value alone is not proof that every RSA-PSS parameter is valid or compliant.
- The classifier uses the signature OID as the primary algorithm identifier. It does not verify the certificate's cryptographic signature, validate the complete certificate chain, assess issuer trust, or determine whether the signature was negotiated or used in a TLS handshake.
- The certificate signature algorithm is also distinct from TLS handshake signature algorithms. This assessment concerns the signature on the certificate itself, not the signature scheme selected for a particular TLS handshake.
- Missing or unrecognized evidence returns `unknown`. This means the current classifier cannot make a supported classification; it does not, by itself, prove that the signature algorithm is insecure.

Integration tests exercise certificate generation, DER encoding, parsing, and classification using the metadata extracted by the certificate parser. Unit tests cover recognized classical algorithms, SHA-1 exclusions, RSA-PSS hash evidence, ML-DSA OIDs, and missing or unrecognized inputs. These tests verify the implemented rules and data flow; they do not constitute a complete cryptographic validation of certificates or signature parameters.

