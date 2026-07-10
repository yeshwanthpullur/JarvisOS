"""Command execution context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from commands.command_permissions import CommandPermission


@dataclass(slots=True)
class CommandContext:
    """Context for command dispatch."""

    command_name: str
    arguments: tuple[str, ...] = ()
    flags: dict[str, str | bool] = field(default_factory=dict)
    conversation_context: Any | None = None
    session_context: Any | None = None
    execution_context: Any | None = None
    permissions: tuple[CommandPermission, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)

