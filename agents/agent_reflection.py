"""Reflection interfaces for future agents."""

from __future__ import annotations


from typing import Any


class AgentReflectionInterface:
    """No-AI reflection interface placeholder."""

    def reflect(self, payload: dict[str, Any] | None = None) -> None:
        """Future reflection hook."""
        raise NotImplementedError("Agent reflection is not implemented yet.")
