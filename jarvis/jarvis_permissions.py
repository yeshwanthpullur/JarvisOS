"""Executive permission metadata."""

from __future__ import annotations

from enum import StrEnum


class JarvisPermission(StrEnum):
    """Declarative permissions available to the Executive Core."""

    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    TASKS = "tasks"
    PLUGINS = "plugins"
    PROVIDERS = "providers"
    AGENTS = "agents"
    AGENT_CREATOR = "agent_creator"
    CONFIGURATION = "configuration"
    HEALTH = "health"
    METRICS = "metrics"

