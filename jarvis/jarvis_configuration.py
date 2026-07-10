"""Configuration model for Executive JARVIS."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JarvisConfiguration:
    """Configuration defaults for Executive JARVIS."""

    enabled: bool = True
    max_history: int = 1000
    default_strategy: str = "direct"
    allow_dynamic_agent_requests: bool = True

