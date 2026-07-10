"""Request pipeline helpers for conversation input."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from conversation.conversation_request import ConversationRequest


class RequestBuilder:
    """Builds conversation requests."""

    initialized = True

    def build(self, text: str) -> ConversationRequest:
        """Build a request."""
        return ConversationRequest(user_input=text, normalized_input=text.strip().lower(), goal=text.strip())


class ContextBuilder:
    """Builds execution context metadata."""

    initialized = True

    def build(self, request: ConversationRequest) -> dict[str, Any]:
        """Build context metadata."""
        return {"goal": request.goal, "priority": request.priority}


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """Execution context metadata."""

    strategy: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExecutionSummary:
    """Execution summary metadata."""

    success: bool
    strategy: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ExecutionHistory:
    """Execution history."""

    def __init__(self) -> None:
        self._items: list[ExecutionSummary] = []
        self.initialized = True

    def append(self, summary: ExecutionSummary) -> None:
        """Append execution summary."""
        self._items.append(summary)

    def list_items(self) -> tuple[ExecutionSummary, ...]:
        """List history."""
        return tuple(self._items)

