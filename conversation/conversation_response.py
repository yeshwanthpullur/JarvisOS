"""Conversation response model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from conversation.conversation_state import ConversationState


@dataclass(frozen=True, slots=True)
class ConversationResponse:
    """Response returned by the conversation engine."""

    response: str
    execution_summary: dict[str, Any] = field(default_factory=dict)
    references: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()
    timing: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    conversation_state: ConversationState = ConversationState.RESPONDING
    execution_state: str = "completed"
    should_exit: bool = False
    should_clear: bool = False

