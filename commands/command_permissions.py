"""Command permission metadata."""

from __future__ import annotations

from enum import StrEnum


class CommandPermission(StrEnum):
    """Declarative command permissions."""

    SYSTEM = "system"
    CONVERSATION = "conversation"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    TASK = "task"
    PLUGIN = "plugin"
    PROVIDER = "provider"
    AGENT = "agent"
    DEPARTMENT = "department"
    WORKFLOW = "workflow"
    CONFIGURATION = "configuration"
    UTILITY = "utility"
    DIAGNOSTIC = "diagnostic"
    DEVELOPER = "developer"

