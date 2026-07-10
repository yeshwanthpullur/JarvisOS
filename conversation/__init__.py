"""Conversation Engine package for JARVIS OS."""

from conversation.conversation_context import ConversationContext
from conversation.conversation_request import ConversationRequest
from conversation.conversation_response import ConversationResponse
from conversation.conversation_session import ConversationSession
from conversation.conversation_state import ConversationState

__all__ = [
    "ConversationContext",
    "ConversationEngine",
    "ConversationManager",
    "ConversationRequest",
    "ConversationResponse",
    "ConversationSession",
    "ConversationState",
    "ConversationStatistics",
]


def __getattr__(name: str) -> object:
    """Lazily expose manager and engine classes to avoid import cycles."""
    if name == "ConversationEngine":
        from conversation.conversation_engine import ConversationEngine

        return ConversationEngine
    if name in {"ConversationManager", "ConversationStatistics"}:
        from conversation.conversation_manager import ConversationManager, ConversationStatistics

        return {"ConversationManager": ConversationManager, "ConversationStatistics": ConversationStatistics}[name]
    raise AttributeError(name)
