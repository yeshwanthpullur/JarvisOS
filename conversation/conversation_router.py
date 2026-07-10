"""Conversation router."""

from __future__ import annotations

from conversation.conversation_request import ConversationRequest


class ConversationRouter:
    """Routes conversation requests to command or natural language handling."""

    initialized = True

    def route(self, request: ConversationRequest) -> str:
        """Return route name."""
        return "command" if request.normalized_input.startswith("/") else "executive"

