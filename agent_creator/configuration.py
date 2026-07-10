"""Configuration models for generated agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentCreatorConfiguration:
    """Configuration metadata used during agent creation."""

    defaults: dict[str, Any] = field(default_factory=dict)
    overrides: dict[str, Any] = field(default_factory=dict)
    environment_variables: tuple[str, ...] = ()
    feature_flags: dict[str, bool] = field(default_factory=dict)
    experimental_options: dict[str, Any] = field(default_factory=dict)
    schema_version: str = "0.1"

    def merged(self) -> dict[str, Any]:
        """Return defaults with overrides applied."""
        data = dict(self.defaults)
        data.update(self.overrides)
        return data

