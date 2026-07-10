"""Command manager."""

from __future__ import annotations

from commands.builtin_commands import register_builtin_commands
from commands.command_aliases import CommandAliases
from commands.command_dispatcher import CommandDispatcher
from commands.command_help import CommandHelp
from commands.command_history import CommandHistory
from commands.command_logger import CommandLogger
from commands.command_metrics import CommandMetrics
from commands.command_parser import CommandParser
from commands.command_registry import CommandRegistry
from conversation.conversation_response import ConversationResponse


class CommandManager:
    """Coordinates command parsing, validation, dispatch, help, and history."""

    def __init__(self) -> None:
        self.registry = CommandRegistry()
        self.parser = CommandParser()
        self.aliases = CommandAliases()
        self.dispatcher = CommandDispatcher(self.registry)
        self.history = CommandHistory()
        self.metrics = CommandMetrics()
        self.logger = CommandLogger()
        self.help = CommandHelp()
        self.initialized = False

    def initialize(self) -> None:
        """Register built-in commands."""
        register_builtin_commands(self.registry)
        self.metrics.registered_commands = len(self.registry.list_commands())
        self.initialized = True

    def execute(self, text: str, conversation_context: object | None = None) -> ConversationResponse:
        """Execute input as a command."""
        parsed = self.parser.parse(text)
        resolved_name = self.aliases.resolve(parsed.name)
        if resolved_name != parsed.name:
            parsed = self.parser.parse(resolved_name + (" " + " ".join(parsed.arguments) if parsed.arguments else ""))
        response = self.dispatcher.dispatch(parsed, conversation_context or self)
        self.history.append(parsed, response)
        if response.warnings:
            self.metrics.commands_failed += 1
        else:
            self.metrics.commands_executed += 1
        return response

    def statistics(self) -> dict[str, int]:
        """Return command statistics."""
        return {
            "registered_commands": len(self.registry.list_commands()),
            "commands_executed": self.metrics.commands_executed,
            "commands_failed": self.metrics.commands_failed,
        }
