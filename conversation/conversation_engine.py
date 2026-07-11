"""Conversation engine."""

from __future__ import annotations

from jarvis import JarvisRequest

from conversation.conversation_context import ConversationContext
from conversation.conversation_request import ConversationRequest
from conversation.conversation_response import ConversationResponse
from conversation.conversation_router import ConversationRouter
from conversation.conversation_state import ConversationState
from conversation.conversation_validator import ConversationValidator


class ConversationEngine:
    """Coordinates conversation input with commands and Executive JARVIS."""

    def __init__(self) -> None:
        self.router = ConversationRouter()
        self.validator = ConversationValidator()
        self.initialized = True

    def handle(self, request: ConversationRequest, context: ConversationContext) -> ConversationResponse:
        """Handle a conversation request."""
        validation = self.validator.validate_request(request)
        if not validation.valid:
            return ConversationResponse(response=validation.errors[0], warnings=validation.errors, conversation_state=ConversationState.FAILED)
        personal_manager = context.metadata.get("personal_intelligence_manager")
        if personal_manager is not None and hasattr(personal_manager, "detect_candidates"):
            try:
                personal_manager.detect_candidates(
                    request.user_input,
                    source_reference=context.session.conversation_id,
                    conversation_id=context.session.conversation_id,
                    request_id=request.timestamp.isoformat() if hasattr(request.timestamp, "isoformat") else None,
                )
            except Exception:
                pass
        if context.command_manager is not None:
            parsed = context.command_manager.parser.parse(request.normalized_input)
            if context.command_manager.registry.lookup(parsed.name) is not None:
                return context.command_manager.execute(request.normalized_input, context)
        route = self.router.route(request)
        if route == "command" and context.command_manager is not None:
            return context.command_manager.execute(request.normalized_input.lstrip("/"), context)
        if context.jarvis_core is None:
            return ConversationResponse(response="Executive JARVIS is not available.", conversation_state=ConversationState.FAILED)
        metadata = dict(context.metadata)
        jarvis_response = context.jarvis_core.handle(
            JarvisRequest(
                content=request.user_input,
                conversation_id=context.session.conversation_id,
                metadata=metadata,
            )
        )
        return ConversationResponse(
            response=jarvis_response.content,
            execution_summary=jarvis_response.execution_summary,
            references=jarvis_response.references,
            warnings=jarvis_response.warnings,
            diagnostics=jarvis_response.diagnostics,
            metadata=jarvis_response.streaming_metadata,
            conversation_state=ConversationState.RESPONDING,
        )
