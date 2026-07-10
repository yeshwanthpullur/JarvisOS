"""Conversation history store."""

from __future__ import annotations

from conversation.conversation_request import ConversationRequest
from conversation.conversation_response import ConversationResponse


class ConversationHistory:
    """In-memory conversation history with search and replay hooks."""

    def __init__(self) -> None:
        self._records: list[tuple[ConversationRequest, ConversationResponse]] = []
        self.initialized = True

    def append(self, request: ConversationRequest, response: ConversationResponse) -> None:
        """Append a conversation turn."""
        self._records.append((request, response))

    def search(self, text: str) -> tuple[tuple[ConversationRequest, ConversationResponse], ...]:
        """Search prior turns by text."""
        needle = text.lower()
        return tuple(record for record in self._records if needle in record[0].normalized_input)

    def summarize(self) -> str:
        """Return a simple deterministic summary."""
        return f"{len(self._records)} conversation turns recorded."

    def export(self) -> tuple[tuple[ConversationRequest, ConversationResponse], ...]:
        """Export records."""
        return tuple(self._records)

    def replay(self) -> tuple[str, ...]:
        """Replay user inputs."""
        return tuple(record[0].user_input for record in self._records)

    def restore(self, records: tuple[tuple[ConversationRequest, ConversationResponse], ...]) -> None:
        """Restore records."""
        self._records = list(records)

    def statistics(self) -> dict[str, int]:
        """Return history statistics."""
        return {"turns": len(self._records)}

