"""Planning interfaces for future agents."""

from __future__ import annotations


from typing import Any


class AgentPlanningInterface:
    """No-AI planning interface placeholder."""

    def plan(self, payload: dict[str, Any] | None = None) -> None:
        """Future planning hook."""
        raise NotImplementedError("Agent planning is not implemented yet.")
