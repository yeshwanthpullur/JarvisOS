"""Conversation context object."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from conversation.conversation_session import ConversationSession


@dataclass(slots=True)
class ConversationContext:
    """Context passed through conversation and command components."""

    session: ConversationSession
    jarvis_core: Any | None = None
    command_manager: Any | None = None
    memory_manager: Any | None = None
    knowledge_manager: Any | None = None
    task_manager: Any | None = None
    task_intelligence_manager: Any | None = None
    goal_intelligence_manager: Any | None = None
    workflow_manager: Any | None = None
    retrieval_manager: Any | None = None
    research_manager: Any | None = None
    plugin_manager: Any | None = None
    provider_manager: Any | None = None
    provider_router: Any | None = None
    agent_manager: Any | None = None
    agent_creator: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
