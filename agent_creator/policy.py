"""Policy engine architecture for Agent Creator."""

from __future__ import annotations

from agent_creator.security import SecurityPolicy


class PolicyEngine:
    """Loads and validates declarative policies."""

    def __init__(self) -> None:
        self._policies: list[SecurityPolicy] = []
        self.initialized = True

    def load_policy(self, policy: SecurityPolicy) -> None:
        """Load a policy."""
        self._policies.append(policy)

    def list_policies(self) -> tuple[SecurityPolicy, ...]:
        """List loaded policies."""
        return tuple(self._policies)

