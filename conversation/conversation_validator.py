"""Conversation validation."""

from __future__ import annotations

from dataclasses import dataclass

from conversation.conversation_request import ConversationRequest


@dataclass(frozen=True, slots=True)
class ConversationValidationResult:
    """Conversation validation result."""

    valid: bool
    errors: tuple[str, ...] = ()


class ConversationValidator:
    """Validates conversation requests."""

    initialized = True

    def validate_request(self, request: ConversationRequest) -> ConversationValidationResult:
        """Validate a conversation request."""
        if not request.normalized_input:
            return ConversationValidationResult(False, ("Input is required.",))
        return ConversationValidationResult(True)

