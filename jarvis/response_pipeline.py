"""Response pipeline helpers."""

from __future__ import annotations

from conversation.conversation_response import ConversationResponse


class ResponseComposer:
    """Composes responses."""

    initialized = True

    def compose(self, text: str) -> ConversationResponse:
        """Compose response."""
        return ConversationResponse(response=text)


class ResponseValidator:
    """Validates responses."""

    initialized = True

    def validate(self, response: ConversationResponse) -> bool:
        """Return response validity."""
        return bool(response.response or response.should_clear)


class ResponseFormatter:
    """Formats responses."""

    initialized = True

    def format(self, response: ConversationResponse) -> str:
        """Return display text."""
        return response.response


class ResponseRenderer:
    """Renders responses for future rich output."""

    initialized = True

    def render(self, response: ConversationResponse) -> str:
        """Render response."""
        return response.response

