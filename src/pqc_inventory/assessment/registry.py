"""Registry for assessment policies."""

from pqc_inventory.assessment.interfaces import AssessmentPolicy


class AssessmentPolicyRegistry:
    """Register and retrieve assessment policies by their identifiers."""

    def __init__(self) -> None:
        self._policies: dict[str, AssessmentPolicy] = {}

    def register(self, policy: AssessmentPolicy) -> None:
        """Register a policy, rejecting duplicate identifiers."""
        policy_id = policy.policy_id

        if policy_id in self._policies:
            raise ValueError(f"Assessment policy {policy_id!r} is already registered.")

        self._policies[policy_id] = policy

    def get(self, policy_id: str) -> AssessmentPolicy:
        """Return a registered policy by identifier."""

        try:
            return self._policies[policy_id]
        except KeyError:
            raise KeyError(
                f"Assessment policy {policy_id!r} is not registered."
            ) from None

    def all(self) -> tuple[AssessmentPolicy, ...]:
        """Return registered policies in registration order."""
        return tuple(self._policies.values())
