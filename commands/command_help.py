"""Command help generator."""

from __future__ import annotations

from commands.command_registry import CommandRegistry


class CommandHelp:
    """Generates help text from the registry."""

    initialized = True

    def render(self, registry: CommandRegistry) -> str:
        """Render help."""
        names = sorted(record.name for record in registry.list_commands() if record.enabled)
        return "Available commands: " + ", ".join(names)

