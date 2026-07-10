"""Command history."""

from __future__ import annotations

from commands.command_parser import ParsedCommand
from conversation.conversation_response import ConversationResponse


class CommandHistory:
    """Stores command execution history."""

    def __init__(self) -> None:
        self._records: list[tuple[ParsedCommand, ConversationResponse]] = []
        self.initialized = True

    def append(self, command: ParsedCommand, response: ConversationResponse) -> None:
        """Append command result."""
        self._records.append((command, response))

    def list_history(self) -> tuple[tuple[ParsedCommand, ConversationResponse], ...]:
        """List command history."""
        return tuple(self._records)

    def statistics(self) -> dict[str, int]:
        """Return history statistics."""
        return {"commands": len(self._records)}

