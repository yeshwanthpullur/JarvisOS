"""Command dispatcher."""

from __future__ import annotations

from commands.command_context import CommandContext
from commands.command_parser import ParsedCommand
from commands.command_registry import CommandRegistry
from commands.command_validator import CommandValidator
from conversation.conversation_response import ConversationResponse


class CommandDispatcher:
    """Validates and dispatches commands."""

    def __init__(self, registry: CommandRegistry, validator: CommandValidator | None = None) -> None:
        self.registry = registry
        self.validator = validator or CommandValidator()
        self.initialized = True

    def dispatch(self, parsed: ParsedCommand, conversation_context: object | None = None) -> ConversationResponse:
        """Dispatch a parsed command."""
        validation = self.validator.validate(parsed, self.registry)
        if not validation.valid:
            return ConversationResponse(response=validation.errors[0], warnings=validation.errors)
        record = self.registry.lookup(parsed.name)
        if record is None:
            return ConversationResponse(response=f"Unknown command: {parsed.name}", warnings=(parsed.name,))
        context = CommandContext(
            command_name=record.name,
            arguments=parsed.arguments,
            flags=parsed.flags,
            conversation_context=conversation_context,
            permissions=record.permissions,
        )
        return record.handler(context)

