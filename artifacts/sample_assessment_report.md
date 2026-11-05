



# TLS Cryptographic Assessment Report

**Sample Assessment**

---

## Report Information

| Field | Value |
|---|---|
| Report ID | `b5631c2b-6e72-4791-8532-01eefdef661e` |
| Report Version | 1.0 |
| Generated | 2026-11-04T17:37:25.826280Z |
| Prepared By | PQC Assessment Framework |
| Organization | Sample Assessment |
| Methodology Version(s) | 1.0 |

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Assessment Overview](#2-assessment-overview)
   - [Policy Execution Results](#21-policy-execution-results)
   - [TLS Collection Results](#22-tls-collection-results)
   - [Assessment Methodology](#23-assessment-methodology)
3. [Detailed Assessment Results](#3-detailed-assessment-results)
   - [Target 1: google.com](#target-1)
4. [Assessment Methodology and Classification](#4-assessment-methodology-and-classification)
5. [Limitations and Considerations](#5-limitations-and-considerations)
6. [Report Conclusion](#6-report-conclusion)

---

# 1. Executive Summary

This report presents the results of a cryptographic assessment
based on collected TLS evidence and the assessment policies
available in the configured assessment framework.

The assessment evaluates observed cryptographic configurations,
records policy findings, and identifies areas requiring further
investigation.

## 1.1 Assessment Summary

| Metric | Result |
|---|---:|
| Total Assessment Runs | 1 |
| Policy Identifiers Represented | 1 |
| Policy Identifiers | A1 |

## 1.2 Finding Classification Summary

| Classification | Count |
|---|---:|
| 🟢 Acceptable | 2 |
| 🟠 Acceptable with Review | 2 |
| 🔴 Unacceptable | 0 |
| ⚪ Unknown | 0 |

> **Interpretation:** These classifications represent individual
> assessment findings. They should not be interpreted as an
> aggregate security rating or overall PQC readiness score.

---

# 2. Assessment Overview

## 2.1 Policy Execution Results

| Execution Status | Count |
|---|---:|
| Completed | 1 |
| Partial | 0 |
| Failed | 0 |
| Not Assessed | 0 |

## 2.2 TLS Collection Results

| Collection Status | Count |
|---|---:|
| Completed | 1 |
| Partial | 0 |
| Failed | 0 |

## 2.3 Assessment Methodology

The following methodology versions are represented in this report:

- `1.0`

### Policies Represented

- `A1`

---

# 3. Detailed Assessment Results

This section presents the assessment results for each target.
Each target is presented in a collapsible section to make
large reports easier to navigate.


<a id="target-1"></a>

<details>
<summary><strong>Target 1: google.com</strong> — 🟢 Completed</summary>

## Assessment Information

| Field | Value |
|---|---|
| Assessment Run ID | `16d8f359-838d-461a-9eba-7b78ad147582` |
| Target | google.com |
| Target Type | domain |
| Port | 443 |
| Assessment Date | 2026-11-04T17:37:25.781029Z |
| Methodology Version | 1.0 |
| Collection Status | 🟢 Completed |

## Policy Results


### A1

| Field | Value |
|---|---|
| Policy ID | `A1` |
| Policy Version | 1.0.0 |
| Execution Status | 🟢 Completed |


#### Findings Summary

| Rule | Dimension | Observed Value | Classification |
|---|---|---|---|
| `A1.1` | tls_version | TLSv1.3 | 🟢 Acceptable |
| `A1.2` | cipher_suite | TLS_AES_256_GCM_SHA384 | 🟢 Acceptable |
| `A1.3` | public_key_algorithm | EC | 🟠 Acceptable with Review |
| `A1.4` | certificate_signature | 1.2.840.10045.4.3.2 | 🟠 Acceptable with Review |

#### Finding Details


**Finding: `A1-tls_version`**

| Field | Value |
|---|---|
| Rule | `A1.1` |
| Dimension | tls_version |
| Classification | 🟢 Acceptable |
| Observed Value | TLSv1.3 |

**Rationale**

TLS 1.3 is the preferred modern TLS version.

**Evidence References**

- `tls.tls_version`


**Finding: `A1-cipher_suite`**

| Field | Value |
|---|---|
| Rule | `A1.2` |
| Dimension | cipher_suite |
| Classification | 🟢 Acceptable |
| Observed Value | TLS_AES_256_GCM_SHA384 |

**Rationale**

The TLS 1.3 cipher suite is in the project's recognized AEAD allowlist.

**Evidence References**

- `tls.cipher_suite`
- `tls.tls_version`


**Finding: `A1-public_key_algorithm`**

| Field | Value |
|---|---|
| Rule | `A1.3` |
| Dimension | public_key_algorithm |
| Classification | 🟠 Acceptable with Review |
| Observed Value | EC |

**Rationale**

EC is a classical public-key algorithm requiring post-quantum migration review.

**Evidence References**

- `tls.public_key_algorithm`


**Finding: `A1-certificate_signature`**

| Field | Value |
|---|---|
| Rule | `A1.4` |
| Dimension | certificate_signature |
| Classification | 🟠 Acceptable with Review |
| Observed Value | 1.2.840.10045.4.3.2 |

**Rationale**

The certificate uses a recognized classical signature algorithm requiring post-quantum migration review.

**Evidence References**

- `tls.certificate_signature_algorithm_oid`
- `tls.certificate_signature_hash_algorithm`




---



## Collection Evidence

### TLS Configuration

| Property | Observed Value |
|---|---|
| TLS Version | TLSv1.3 |
| Cipher Suite | TLS_AES_256_GCM_SHA384 |
| Cipher Strength | 256 |
| Key Establishment Group | X25519 |
| Key Establishment Source | openssl_s_client_separate_handshake |
| Key Establishment Evidence Status | observed |

### Certificate Information

| Property | Observed Value |
|---|---|
| Certificate Version | v3 |
| Serial Number | 217138846515957589284893936179616346089 |
| Public Key Algorithm | EC |
| Public Key Variant | Not available |
| Public Key Algorithm OID | 1.2.840.10045.2.1 |
| Key Size | 256 |
| Public Key Curve | secp256r1 |
| RSA Public Exponent | Not available |
| Signature Algorithm OID | 1.2.840.10045.4.3.2 |
| Signature Hash Algorithm | sha256 |
| Not Before | 2026-09-28T18:38:33+00:00 |
| Not After | 2026-12-21T18:38:32+00:00 |
| Certificate Verification | verified |

### Certificate Extensions

**Subject Alternative DNS Names**

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

**Subject Alternative IP Addresses**

- No IP addresses recorded.

**Key Usage**

- digital_signature: Enabled
- content_commitment: Disabled
- key_encipherment: Disabled
- data_encipherment: Disabled
- key_agreement: Disabled
- key_cert_sign: Disabled
- crl_sign: Disabled

**Extended Key Usage**

- 1.3.6.1.5.5.7.3.1

**Basic Constraints**

- ca: False
- path_length: None

### Certificate Subject

- **2.5.4.3:** *.google.com

### Certificate Issuer

- **2.5.4.6:** US
- **2.5.4.10:** Google Trust Services
- **2.5.4.3:** WE2

## Collection Diagnostics


No collection diagnostics were recorded.


</details>

---


# 4. Assessment Methodology and Classification

Assessment findings are generated using the rules implemented
in the configured assessment policies.

Each finding includes:

- A policy identifier and version.
- An assessment rule identifier.
- An observed value, where available.
- A classification.
- A rationale explaining the classification.
- References to supporting evidence.

## 4.1 Classification Definitions

| Classification | Description |
|---|---|
| 🟢 Acceptable | Meets the applicable implemented assessment rule. |
| 🟠 Acceptable with Review | Requires further security review or consideration. |
| 🔴 Unacceptable | Does not meet the applicable assessment rule. |
| ⚪ Unknown | Available evidence is insufficient or unsupported. |

These classifications are project-specific assessment outcomes.
They do not independently establish regulatory compliance or
comprehensive cryptographic security.

## 4.2 Evidence Interpretation

Assessment conclusions depend on the evidence collected and
the rules implemented by each policy.

Missing, incomplete, or unavailable evidence must not automatically
be interpreted as proof of either security or insecurity.

---

# 5. Limitations and Considerations

The following considerations apply when interpreting this report:

- Assessment results are limited to the evidence available for each target.
- Collection failures and incomplete scans may affect assessment coverage.
- Policy findings reflect implemented rules and their documented scope.
- TLS observations do not reveal every cryptographic dependency within an organization.
- Certificate metadata alone does not establish complete certificate-chain trust or hostname validity.
- Key-establishment observations must be interpreted according to their collection source.
- The absence of a finding does not necessarily establish that a system is secure.
- PQC readiness requires broader organizational and application-level evidence.

Further investigation may be necessary before making security,
compliance, or migration decisions.

---

# 6. Report Conclusion

This report provides a structured record of the collected cryptographic
evidence and the assessment results produced by the configured policies.

The findings should support further security analysis,
cryptographic inventory development, and post-quantum migration planning.

They should not be treated as a substitute for a comprehensive
cryptographic assessment or an independently validated security audit.

---

*End of Report*

**Report ID:** `b5631c2b-6e72-4791-8532-01eefdef661e`
**Report Version:** 1.0
**Generated:** 2026-11-04T17:37:25.826280Z
