"""Conversation summary model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConversationSummary:
    """Summary of a conversation."""

    conversation_id: str
    turns: int
    active_topic: str | None = None
    active_goal: str | None = None

