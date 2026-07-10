"""Agent configuration containers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AgentConfiguration:
    """Merged configuration for one agent."""

    defaults: dict[str, Any] = field(default_factory=dict)
    overrides: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Return an override, default, or fallback value."""
        if key in self.overrides:
            return self.overrides[key]
        return self.defaults.get(key, default)
