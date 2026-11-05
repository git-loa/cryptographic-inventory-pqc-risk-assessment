"""
A1 policy: TLS configuration quality.

Evaluates negotiated TLS version, cipher suite, certificate public-key
algorithm, and certificate signature algorithm.

This policy evaluates supplied evidence only. It does not perform
network scans, persist results, or calculate an aggregate score.
"""

from pqc_inventory.assessment.interfaces import AssessmentPolicy
from pqc_inventory.assessment.models import (
    AssessmentContext,
    AssessmentFinding,
    PolicyMetadata,
    PolicyResult,
    PolicyRule,
)
from pqc_inventory.assessment.policies.a1_classifiers import (
    classify_certificate_signature,
    classify_cipher_suite,
    classify_public_key_algorithm,
    classify_tls_version,
)


class A1TLSConfigurationPolicy(AssessmentPolicy):
    """Assess four dimensions of TLS configuration quality."""

    POLICY_ID = "A1"
    POLICY_NAME = "TLS Configuration Quality"
    POLICY_VERSION = "1.0.0"
    POLICY_DESCRIPTION = (
        "Assesses negotiated TLS version, cipher suite, certificate "
        "public-key algorithm, and certificate signature algorithm "
        "using explicit, evidence-based classification rules."
    )

    @property
    def policy_id(self) -> str:
        """Return the stable identifier for this policy."""
        return self.POLICY_ID

    @property
    def policy_version(self) -> str:
        """Return the policy implementation version."""
        return self.POLICY_VERSION

    @property
    def policy_name(self) -> str:
        """Return the human-readable policy name."""
        return self.POLICY_NAME

    @property
    def policy_description(self) -> str:
        """Return the policy's assessment scope."""
        return self.POLICY_DESCRIPTION

    def assess(self, context: AssessmentContext) -> PolicyResult:
        """Evaluate TLS evidence and return standardized findings."""
        tls = context["tls"]

        findings = self._build_findings(tls)
        execution_status, limitations = self._get_execution_status(tls)

        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "execution_status": execution_status,
            "findings": findings,
            "limitations": limitations,
        }

    @property
    def metadata(self) -> PolicyMetadata:
        """Return descriptive metadata and rules for the A1 policy."""

        return PolicyMetadata(
            policy_id=self.POLICY_ID,
            name=self.POLICY_NAME,
            version=self.POLICY_VERSION,
            description=self.POLICY_DESCRIPTION,
            scope=(
                "Negotiated TLS protocol version",
                "Negotiated TLS cipher suite",
                "Certificate public-key algorithm",
                "Certificate signature algorithm",
            ),
            rules=(
                PolicyRule(
                    rule_id="A1.1",
                    name="TLS Protocol Version",
                    description=(
                        "Evaluates the security classification of the "
                        "negotiated TLS protocol version."
                    ),
                    dimension="tls_version",
                    evaluation_summary=(
                        "TLS 1.3 is acceptable; TLS 1.2 is acceptable "
                        "with review; TLS 1.0, TLS 1.1, SSLv2, and SSLv3 "
                        "are unacceptable. Missing or unrecognized "
                        "evidence is classified as unknown."
                    ),
                ),
                PolicyRule(
                    rule_id="A1.2",
                    name="Cipher Suite Security",
                    description=(
                        "Evaluates the negotiated cipher suite using "
                        "the negotiated TLS protocol version."
                    ),
                    dimension="cipher_suite",
                    evaluation_summary=(
                        "Explicitly excluded cipher-suite patterns are "
                        "unacceptable. Recognized TLS 1.3 AEAD suites "
                        "are acceptable, except CCM_8, which requires "
                        "review. Recognized TLS 1.2 ECDHE-AEAD suites "
                        "are acceptable; static RSA and ECDHE-CBC suites "
                        "require review. Unrecognized combinations "
                        "are classified as unknown."
                    ),
                ),
                PolicyRule(
                    rule_id="A1.3",
                    name="Certificate Public-Key Algorithm",
                    description=(
                        "Evaluates the certificate public-key algorithm "
                        "and its implications for post-quantum migration."
                    ),
                    dimension="public_key_algorithm",
                    evaluation_summary=(
                        "ML-DSA is acceptable. RSA, EC, Ed25519, and "
                        "Ed448 are acceptable with review because they "
                        "are classical algorithms. DSA is unacceptable. "
                        "Missing or unrecognized algorithms are unknown."
                    ),
                ),
                PolicyRule(
                    rule_id="A1.4",
                    name="Certificate Signature Algorithm",
                    description=(
                        "Evaluates the certificate signature algorithm "
                        "using its object identifier and relevant hash evidence."
                    ),
                    dimension="certificate_signature",
                    evaluation_summary=(
                        "Recognized SHA-1 signature OIDs are unacceptable. "
                        "Recognized classical RSA, ECDSA, and EdDSA "
                        "signatures require post-quantum migration review. "
                        "RSA-PSS requires a recognized SHA-256, SHA-384, "
                        "or SHA-512 hash. Recognized ML-DSA signature "
                        "OIDs are acceptable. Other or insufficient "
                        "evidence is classified as unknown."
                    ),
                ),
            ),
        )

    def _build_findings(self, tls: dict) -> list[AssessmentFinding]:
        """Classify TLS evidence and build the four A1 findings."""
        classifications = self._classify_dimensions(tls)

        return [
            self._create_finding(rule_id, dimension, result)
            for rule_id, dimension, result in classifications
        ]

    @staticmethod
    def _classify_dimensions(tls: dict) -> list[tuple[str, str, dict[str, str]]]:
        """Apply the classification rules to the supplied TLS evidence."""
        tls_version = tls.get("tls_version")

        return [
            (
                "A1.1",
                "tls_version",
                classify_tls_version(tls_version),
            ),
            (
                "A1.2",
                "cipher_suite",
                classify_cipher_suite(
                    tls.get("cipher_suite"),
                    tls_version,
                ),
            ),
            (
                "A1.3",
                "public_key_algorithm",
                classify_public_key_algorithm(
                    tls.get("public_key_algorithm"),
                ),
            ),
            (
                "A1.4",
                "certificate_signature",
                classify_certificate_signature(
                    tls.get("certificate_signature_algorithm_oid"),
                    tls.get("certificate_signature_hash_algorithm"),
                ),
            ),
        ]

    def _create_finding(
        self,
        rule_id: str,
        dimension: str,
        result: dict[str, str],
    ) -> AssessmentFinding:
        """Convert one classification into a standardized finding."""
        observed = result["observed"]

        evidence_references = {
            "tls_version": ["tls.tls_version"],
            "cipher_suite": [
                "tls.cipher_suite",
                "tls.tls_version",
            ],
            "public_key_algorithm": ["tls.public_key_algorithm"],
            "certificate_signature": [
                "tls.certificate_signature_algorithm_oid",
                "tls.certificate_signature_hash_algorithm",
            ],
        }

        return {
            "finding_id": f"A1-{dimension}",
            "policy_id": self.policy_id,
            "dimension": dimension,
            "observed_value": observed if observed != "unknown" else None,
            "classification": result["classification"],
            "rule_id": rule_id,
            "rationale": result["reason"],
            "evidence_references": evidence_references[dimension],
        }

    @staticmethod
    def _get_execution_status(tls: dict) -> tuple[str, list[str]]:
        """Determine policy execution status from the scan outcome."""
        scan_status = tls.get("scan_status")

        if scan_status == "completed":
            return ("completed", [])

        if scan_status == "partial":
            return (
                "partial",
                [
                    "The TLS scan completed partially; "
                    "some evidence may be unavailable."
                ],
            )

        if scan_status == "failed":
            return (
                "partial",
                ["The TLS scan failed; " "available evidence may be incomplete."],
            )
        return (
            "partial",
            ["The scan outcome is missing or unrecognized."],
        )
