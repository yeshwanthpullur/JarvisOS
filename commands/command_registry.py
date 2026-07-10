"""Command registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from commands.command_context import CommandContext
from commands.command_permissions import CommandPermission
from conversation.conversation_response import ConversationResponse


CommandHandler = Callable[[CommandContext], ConversationResponse]


@dataclass(slots=True)
class CommandRecord:
    """Registered command metadata."""

    name: str
    handler: CommandHandler
    description: str
    category: str
    aliases: tuple[str, ...] = ()
    permissions: tuple[CommandPermission, ...] = ()
    enabled: bool = True
    version: str = "0.1.0"
    metadata: dict[str, object] = field(default_factory=dict)


class CommandRegistry:
    """Registers and looks up commands."""

    def __init__(self) -> None:
        self._commands: dict[str, CommandRecord] = {}
        self._aliases: dict[str, str] = {}
        self.initialized = True

    def register(self, record: CommandRecord) -> None:
        """Register a command."""
        self._commands[record.name] = record
        for alias in record.aliases:
            self._aliases[alias] = record.name

    def unregister(self, name: str) -> bool:
        """Unregister a command."""
        removed = self._commands.pop(name, None)
        if removed:
            for alias in removed.aliases:
                self._aliases.pop(alias, None)
        return removed is not None

    def lookup(self, name: str) -> CommandRecord | None:
        """Lookup command or alias."""
        return self._commands.get(self._aliases.get(name, name))

    def enable(self, name: str) -> None:
        """Enable a command."""
        self._commands[name].enabled = True

    def disable(self, name: str) -> None:
        """Disable a command."""
        self._commands[name].enabled = False

    def list_commands(self) -> tuple[CommandRecord, ...]:
        """List registered commands."""
        return tuple(self._commands.values())

    def statistics(self) -> dict[str, int]:
        """Return registry statistics."""
        return {"registered_commands": len(self._commands), "aliases": len(self._aliases)}

