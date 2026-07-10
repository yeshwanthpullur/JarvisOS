"""Plugin configuration containers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PluginConfig:
    """Runtime configuration for a plugin."""

    values: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Return a configuration value."""
        return self.values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self.values[key] = value
