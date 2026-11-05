




# TLS Cryptographic Assessment Report

**Sample Assessment**
*Cryptographic inventory and TLS configuration assessment*

| Report detail | Value |
|---|---|
| Report ID | `bcf9aca7-03e3-468a-9173-81794651c527` |
| Report version | 1.0 |
| Generated | 2026-11-05T16:05:05.632507Z |
| Prepared by | PQC Assessment Framework |
| Organization | Sample Assessment |
| Methodology version(s) | 1.0 |

---

## Contents

1. [Executive summary](#1-executive-summary)
2. [Assessment overview](#2-assessment-overview)
3. [Policy catalogue and methodology](#3-policy-catalogue-and-methodology)
4. [Target assessment results](#4-target-assessment-results)
   - [1. google.com](#target-1)
5. [Classification and interpretation](#5-classification-and-interpretation)
6. [Limitations](#6-limitations)
7. [Conclusion](#7-conclusion)

---

# 1. Executive summary

This report records the TLS evidence collected for the listed targets and the results produced by the assessment policies configured for the assessment run. It is intended to support technical review, cryptographic inventory development, and prioritization of further investigation.

### Assessment at a glance

| Measure | Result |
|---|---:|
| Assessment runs | **1** |
| Distinct policy identifiers | **1** |
| Policies represented | A1 |
| Methodology versions | 1.0 |

### Finding classifications

| Classification | Findings |
|---|---:|
| 🟢 Acceptable | 2 |
| 🟠 Acceptable with Review | 2 |
| 🔴 Unacceptable | 0 |
| ⚪ Unknown | 0 |

> **Interpretation:** These counts summarize individual policy findings. They are not an aggregate security rating, a compliance determination, or a measure of overall post-quantum cryptography (PQC) readiness.

---

# 2. Assessment overview

### Policy execution

| Execution status | Count |
|---|---:|
| 🟢 Completed | 1 |
| 🟠 Partial | 0 |
| 🔴 Failed | 0 |
| ⚪ Not assessed | 0 |

### TLS collection

| Collection status | Count |
|---|---:|
| 🟢 Completed | 1 |
| 🟠 Partial | 0 |
| 🔴 Failed | 0 |

### Assessment coverage

- **Methodology versions:** 1.0
- **Policy identifiers:** A1

---

# 3. Policy catalogue and methodology

This section describes each distinct policy represented in the assessment runs. Policy metadata is presented once; target-specific execution outcomes and findings appear in Section 4.


## 3.1 TLS Configuration Quality (`A1`)

| Policy attribute | Description |
|---|---|
| Policy ID | `A1` |
| Version | 1.0.0 |
| Description | Assesses negotiated TLS version, cipher suite, certificate public-key algorithm, and certificate signature algorithm using explicit, evidence-based classification rules. |
| Scope | Negotiated TLS protocol version; Negotiated TLS cipher suite; Certificate public-key algorithm; Certificate signature algorithm |

### Assessment rules

| Rule | Dimension | Description | Evaluation summary |
|---|---|---|---|
| `A1.1` — TLS Protocol Version | tls_version | Evaluates the security classification of the negotiated TLS protocol version. | TLS 1.3 is acceptable; TLS 1.2 is acceptable with review; TLS 1.0, TLS 1.1, SSLv2, and SSLv3 are unacceptable. Missing or unrecognized evidence is classified as unknown. |
| `A1.2` — Cipher Suite Security | cipher_suite | Evaluates the negotiated cipher suite using the negotiated TLS protocol version. | Explicitly excluded cipher-suite patterns are unacceptable. Recognized TLS 1.3 AEAD suites are acceptable, except CCM_8, which requires review. Recognized TLS 1.2 ECDHE-AEAD suites are acceptable; static RSA and ECDHE-CBC suites require review. Unrecognized combinations are classified as unknown. |
| `A1.3` — Certificate Public-Key Algorithm | public_key_algorithm | Evaluates the certificate public-key algorithm and its implications for post-quantum migration. | ML-DSA is acceptable. RSA, EC, Ed25519, and Ed448 are acceptable with review because they are classical algorithms. DSA is unacceptable. Missing or unrecognized algorithms are unknown. |
| `A1.4` — Certificate Signature Algorithm | certificate_signature | Evaluates the certificate signature algorithm using its object identifier and relevant hash evidence. | Recognized SHA-1 signature OIDs are unacceptable. Recognized classical RSA, ECDSA, and EdDSA signatures require post-quantum migration review. RSA-PSS requires a recognized SHA-256, SHA-384, or SHA-512 hash. Recognized ML-DSA signature OIDs are acceptable. Other or insufficient evidence is classified as unknown. |





---

# 4. Target assessment results

<a id="target-1"></a>

## 4.1 google.com

**Collection status:** 🟢 Completed

<details>
<summary><strong>View assessment and collection details for google.com</strong></summary>

### Assessment record

| Attribute | Value |
|---|---|
| Assessment run ID | `999cfedf-9406-4813-853b-87099f23c4ea` |
| Target | google.com |
| Target type | domain |
| Port | 443 |
| Assessment date | 2026-11-05T16:05:05.570702Z |
| Methodology version | 1.0 |
| Collection status | 🟢 Completed |

### Policy execution results


#### TLS Configuration Quality (`A1`)

| Attribute | Result |
|---|---|
| Policy version | 1.0.0 |
| Execution status | 🟢 Completed |
| Findings recorded | 4 |
| Policy description | Assesses negotiated TLS version, cipher suite, certificate public-key algorithm, and certificate signature algorithm using explicit, evidence-based classification rules. |

**Findings summary**

| Finding ID | Rule | Dimension | Observed value | Classification |
|---|---|---|---|---|
| `A1-tls_version` | `A1.1` | tls_version | TLSv1.3 | 🟢 Acceptable |
| `A1-cipher_suite` | `A1.2` | cipher_suite | TLS_AES_256_GCM_SHA384 | 🟢 Acceptable |
| `A1-public_key_algorithm` | `A1.3` | public_key_algorithm | EC | 🟠 Acceptable with Review |
| `A1-certificate_signature` | `A1.4` | certificate_signature | 1.2.840.10045.4.3.2 | 🟠 Acceptable with Review |

**Finding details**

<details>
<summary><strong>A1-tls_version</strong> — 🟢 Acceptable</summary>

| Attribute | Value |
|---|---|
| Rule ID | `A1.1` |
| Dimension | tls_version |
| Classification | 🟢 Acceptable |
| Observed value | TLSv1.3 |

**Rationale**

TLS 1.3 is the preferred modern TLS version.

**Evidence references**

- `tls.tls_version`
</details>
<details>
<summary><strong>A1-cipher_suite</strong> — 🟢 Acceptable</summary>

| Attribute | Value |
|---|---|
| Rule ID | `A1.2` |
| Dimension | cipher_suite |
| Classification | 🟢 Acceptable |
| Observed value | TLS_AES_256_GCM_SHA384 |

**Rationale**

The TLS 1.3 cipher suite is in the project's recognized AEAD allowlist.

**Evidence references**

- `tls.cipher_suite`
- `tls.tls_version`
</details>
<details>
<summary><strong>A1-public_key_algorithm</strong> — 🟠 Acceptable with Review</summary>

| Attribute | Value |
|---|---|
| Rule ID | `A1.3` |
| Dimension | public_key_algorithm |
| Classification | 🟠 Acceptable with Review |
| Observed value | EC |

**Rationale**

EC is a classical public-key algorithm requiring post-quantum migration review.

**Evidence references**

- `tls.public_key_algorithm`
</details>
<details>
<summary><strong>A1-certificate_signature</strong> — 🟠 Acceptable with Review</summary>

| Attribute | Value |
|---|---|
| Rule ID | `A1.4` |
| Dimension | certificate_signature |
| Classification | 🟠 Acceptable with Review |
| Observed value | 1.2.840.10045.4.3.2 |

**Rationale**

The certificate uses a recognized classical signature algorithm requiring post-quantum migration review.

**Evidence references**

- `tls.certificate_signature_algorithm_oid`
- `tls.certificate_signature_hash_algorithm`
</details>




### TLS connection evidence

| Property | Observed value |
|---|---|
| Negotiated TLS version | TLSv1.3 |
| Cipher suite | TLS_AES_256_GCM_SHA384 |
| Cipher strength | 256 |
| Key-establishment group | X25519 |
| Key-establishment evidence source | openssl_s_client_separate_handshake |
| Key-establishment evidence status | observed |

### Certificate evidence

| Property | Observed value |
|---|---|
| Certificate version | v3 |
| Serial number | 217138846515957589284893936179616346089 |
| Public-key algorithm | EC |
| Public-key variant | Not available |
| Public-key algorithm OID | 1.2.840.10045.2.1 |
| Key size | 256 |
| Public-key curve | secp256r1 |
| RSA public exponent | Not available |
| Certificate signature algorithm OID | 1.2.840.10045.4.3.2 |
| Certificate signature hash algorithm | sha256 |
| Valid from | 2026-09-28T18:38:33+00:00 |
| Valid until | 2026-12-21T18:38:32+00:00 |
| Certificate verification status | verified |

### Certificate extensions

**Subject alternative DNS names**

- `*.google.com`
- `*.appengine.google.com`
- `*.bdn.dev`
- `*.origin-test.bdn.dev`
- `*.cloud.google.com`
- `*.crowdsource.google.com`
- `*.datacompute.google.com`
- `*.google.ca`
- `*.google.cl`
- `*.google.co.in`
- `*.google.co.jp`
- `*.google.co.uk`
- `*.google.com.ar`
- `*.google.com.au`
- `*.google.com.br`
- `*.google.com.co`
- `*.google.com.mx`
- `*.google.com.tr`
- `*.google.com.vn`
- `*.google.de`
- `*.google.es`
- `*.google.fr`
- `*.google.hu`
- `*.google.it`
- `*.google.nl`
- `*.google.pl`
- `*.google.pt`
- `*.gemini.cloud.google.com`
- `*.gstatic.com`
- `*.metric.gstatic.com`
- `*.gvt1.com`
- `*.gcpcdn.gvt1.com`
- `*.gvt2.com`
- `*.gcp.gvt2.com`
- `*.url.google.com`
- `*.youtube-nocookie.com`
- `*.ytimg.com`
- `ai.android`
- `android.com`
- `*.android.com`
- `*.flash.android.com`
- `g.co`
- `*.g.co`
- `goo.gl`
- `www.goo.gl`
- `google-analytics.com`
- `*.google-analytics.com`
- `google.com`
- `googlecommerce.com`
- `*.googlecommerce.com`
- `urchin.com`
- `*.urchin.com`
- `youtu.be`
- `youtube.com`
- `*.youtube.com`
- `music.youtube.com`
- `*.music.youtube.com`
- `youtubeeducation.com`
- `*.youtubeeducation.com`
- `youtubekids.com`
- `*.youtubekids.com`
- `yt.be`
- `*.yt.be`
- `android.clients.google.com`
- `*.aistudio.google.com`

**Subject alternative IP addresses**

- None recorded.

**Key usage**

| Usage | State |
|---|---|
| digital_signature | Enabled |
| content_commitment | Disabled |
| key_encipherment | Disabled |
| data_encipherment | Disabled |
| key_agreement | Disabled |
| key_cert_sign | Disabled |
| crl_sign | Disabled |

**Extended key usage**

- 1.3.6.1.5.5.7.3.1

**Basic constraints**

| Constraint | Value |
|---|---|
| ca | False |
| path_length | Not available |

### Certificate identity

**Subject**

| Attribute | Value |
|---|---|
| 2.5.4.3 | *.google.com |

**Issuer**

| Attribute | Value |
|---|---|
| 2.5.4.6 | US |
| 2.5.4.10 | Google Trust Services |
| 2.5.4.3 | WE2 |

### Collection diagnostics

No collection diagnostics were recorded.

</details>

---

# 5. Classification and interpretation

| Classification | Interpretation |
|---|---|
| 🟢 Acceptable | The observed evidence meets the applicable implemented assessment rule. |
| 🟠 Acceptable with Review | The result requires additional security review or contextual consideration. |
| 🔴 Unacceptable | The observed evidence does not meet the applicable implemented assessment rule. |
| ⚪ Unknown | The available evidence is insufficient or unsupported for a conclusive classification. |

Classifications are policy-specific outcomes. Interpret them in the context of the applicable policy version, rule, evidence, and documented scope. They do not independently establish regulatory compliance or comprehensive cryptographic security.

Missing or incomplete evidence must not automatically be interpreted as proof of either security or insecurity.

---

# 6. Limitations

The following limitations should be considered when interpreting the results:

- Findings are limited to the evidence collected for each target and the rules implemented by the represented policies.
- Partial or failed collection may reduce the evidence available for assessment.
- TLS endpoint observations do not enumerate every cryptographic dependency within an organization.
- Certificate metadata alone does not establish complete certificate-chain trust or hostname validity.
- Key-establishment observations depend on the collection method and recorded evidence source.
- The absence of a finding does not establish that a system is secure.
- PQC readiness requires broader evidence about applications, protocols, cryptographic dependencies, vendors, and migration plans.

Further investigation may be required before making security, compliance, or migration decisions.

---

# 7. Conclusion

This report provides a structured record of the TLS evidence collected and the policy results produced for the assessed targets. It is intended to support technical review, cryptographic inventory development, and prioritization of further investigation.

Interpret findings within the documented scope and limitations of the assessment methodology. This report is not a substitute for a comprehensive cryptographic assessment or an independently validated security audit.

---

*End of report*

**Report ID:** `bcf9aca7-03e3-468a-9173-81794651c527` · **Version:** 1.0 · **Generated:** 2026-11-05T16:05:05.632507Z
