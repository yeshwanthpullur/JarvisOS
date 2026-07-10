"""Conversation metrics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ConversationMetrics:
    """Metrics for conversation and command operation."""

    conversations: int = 0
    commands: int = 0
    requests: int = 0
    responses: int = 0
    sessions: int = 0
    execution_time: float = 0.0
    failures: int = 0
    recoveries: int = 0
    average_response_time: float = 0.0
    history_size: int = 0
    active_sessions: int = 0

