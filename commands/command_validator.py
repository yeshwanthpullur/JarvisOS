"""Command validation."""

from __future__ import annotations

from dataclasses import dataclass

from commands.command_parser import ParsedCommand
from commands.command_registry import CommandRegistry


@dataclass(frozen=True, slots=True)
class CommandValidationResult:
    """Command validation result."""

    valid: bool
    errors: tuple[str, ...] = ()


class CommandValidator:
    """Validates command syntax and registry state."""

    initialized = True

    def validate(self, parsed: ParsedCommand, registry: CommandRegistry) -> CommandValidationResult:
        """Validate parsed command."""
        if not parsed.valid or not parsed.name:
            return CommandValidationResult(False, ("Command name is required.",))
        record = registry.lookup(parsed.name)
        if record is None:
            return CommandValidationResult(False, (f"Unknown command: {parsed.name}",))
        if not record.enabled:
            return CommandValidationResult(False, (f"Command disabled: {parsed.name}",))
        return CommandValidationResult(True)

