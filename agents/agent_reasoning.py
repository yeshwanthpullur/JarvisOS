"""Reasoning interfaces for future agents."""

from __future__ import annotations


from typing import Any


class AgentReasoningInterface:
    """No-AI reasoning interface placeholder."""

    def reason(self, payload: dict[str, Any] | None = None) -> None:
        """Future reasoning hook."""
        raise NotImplementedError("Agent reasoning is not implemented yet.")
