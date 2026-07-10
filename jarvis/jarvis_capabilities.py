"""Executive capability metadata."""

from __future__ import annotations

from enum import StrEnum


class JarvisCapability(StrEnum):
    """Capabilities coordinated by the Executive Core."""

    CONVERSATION = "conversation"
    DECISION_MAKING = "decision_making"
    PLANNING = "planning"
    COORDINATION = "coordination"
    DELEGATION = "delegation"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    TASKS = "tasks"
    PLUGINS = "plugins"
    PROVIDERS = "providers"
    TOOLS = "tools"
    SKILLS = "skills"
    DEPARTMENTS = "departments"
    RESPONSE_COMPOSITION = "response_composition"
    RECOVERY = "recovery"
    HEALTH_MONITORING = "health_monitoring"

