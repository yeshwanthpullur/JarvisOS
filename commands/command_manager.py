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
        if parsed.metadata.get("parse_error") == "unmatched_quotation":
            return ConversationResponse(
                response="Command parse error: unmatched quotation mark.",
                warnings=("command_parse_error",),
                execution_state="failed",
            )
        resolved_name = self.aliases.resolve(parsed.name)
        if resolved_name != parsed.name:
            parsed = self.parser.parse(resolved_name + (" " + " ".join(parsed.arguments) if parsed.arguments else ""))
        if self.registry.lookup(parsed.name) is None:
            namespace_response = self._unknown_namespace_response(parsed.name, parsed.arguments)
            if namespace_response is not None:
                self.history.append(parsed, namespace_response)
                self.metrics.commands_failed += 1
                return namespace_response
        response = self.dispatcher.dispatch(parsed, conversation_context or self)
        self.history.append(parsed, response)
        if response.warnings:
            self.metrics.commands_failed += 1
        else:
            self.metrics.commands_executed += 1
        return response

    def _unknown_namespace_response(self, name: str, arguments: tuple[str, ...]) -> ConversationResponse | None:
        root = name.split(maxsplit=1)[0]
        matches = sorted(record.name for record in self.registry.list_commands() if record.name.startswith(f"{root} "))
        if not matches:
            return None
        suffix = name.split(maxsplit=1)[1:] + list(arguments)
        attempted = " ".join(suffix).strip() or "(missing)"
        preferred = [f"{root} {item}" for item in ("status", "list", "health", "help")]
        ordered = [item for item in preferred if item in matches] + [item for item in matches if item not in preferred]
        suggestions = ", ".join(ordered[:8])
        return ConversationResponse(
            response=f"Unknown {root} command: {attempted}. Try: {suggestions}.",
            warnings=("unknown_command_subcommand",),
            execution_state="failed",
        )

    def is_command_candidate(self, text: str) -> bool:
        """Identify command-shaped input without invoking shell-style parsing."""
        stripped = text.strip().lstrip("/").strip()
        if not stripped:
            return False
        root = stripped.split(maxsplit=1)[0].lower()
        return text.strip().startswith("/") or any(
            record.name == root or record.name.startswith(f"{root} ") or root in record.aliases
            for record in self.registry.list_commands()
        )

    def statistics(self) -> dict[str, int]:
        """Return command statistics."""
        return {
            "registered_commands": len(self.registry.list_commands()),
            "commands_executed": self.metrics.commands_executed,
            "commands_failed": self.metrics.commands_failed,
        }
