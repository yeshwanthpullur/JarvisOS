"""Agent history tracking."""

from __future__ import annotations

from agents.agent_result import AgentResult


class AgentHistory:
    """Stores agent results for future analytics."""

    def __init__(self) -> None:
        self._results: list[AgentResult] = []

    def record(self, result: AgentResult) -> None:
        """Record a result."""
        self._results.append(result)

    def list_results(self) -> tuple[AgentResult, ...]:
        """List results."""
        return tuple(self._results)
