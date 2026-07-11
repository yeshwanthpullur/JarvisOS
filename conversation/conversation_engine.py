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
        context_manager = context.metadata.get("context_intelligence_manager")
        if context_manager is not None and hasattr(context_manager, "prepare_request"):
            try:
                context_resolution = context_manager.prepare_request(request.user_input, context.session)
                context.metadata["resolved_context"] = {
                    "request_type": context_resolution.request_type,
                    "status": context_resolution.status,
                    "confidence": context_resolution.confidence,
                    "active_objective": context_resolution.active_objective,
                    "next_step": context_resolution.next_step,
                    "ambiguity": context_resolution.ambiguity,
                    "stale_reference": context_resolution.stale_reference,
                    "reason": context_resolution.reason,
                    "pending_state": dict(context_resolution.pending_state),
                    "resolved_item": {
                        "identifier": context_resolution.resolved_item.identifier,
                        "context_type": context_resolution.resolved_item.context_type,
                        "value": context_resolution.resolved_item.value,
                        "source": context_resolution.resolved_item.source,
                        "source_reference": context_resolution.resolved_item.source_reference,
                        "confidence": context_resolution.resolved_item.confidence,
                    }
                    if context_resolution.resolved_item is not None
                    else None,
                    "candidates": tuple(
                        {
                            "identifier": item.identifier,
                            "context_type": item.context_type,
                            "value": item.value,
                            "source": item.source,
                            "source_reference": item.source_reference,
                            "confidence": item.confidence,
                        }
                        for item in context_resolution.candidates
                    ),
                }
                if context_resolution.immediate_response is not None:
                    return ConversationResponse(
                        response=context_resolution.immediate_response,
                        execution_summary={
                            "context_request_type": context_resolution.request_type,
                            "context_status": context_resolution.status,
                            "context_confidence": context_resolution.confidence,
                            "active_objective": context_resolution.active_objective,
                            "next_step": context_resolution.next_step,
                            "ambiguity": context_resolution.ambiguity,
                            "stale_reference": context_resolution.stale_reference,
                        },
                        metadata={"resolved_context": context.metadata["resolved_context"]},
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
