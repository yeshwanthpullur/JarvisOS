"""Controller for Executive JARVIS."""

from __future__ import annotations

from jarvis.jarvis_context import JarvisContext
from jarvis.jarvis_decision_engine import JarvisDecisionEngine
from jarvis.jarvis_dispatcher import JarvisDispatcher
from jarvis.jarvis_intent_engine import JarvisIntentEngine
from jarvis.jarvis_planning import JarvisPlanning
from jarvis.jarvis_request import JarvisRequest
from jarvis.jarvis_response import JarvisResponse
from jarvis.jarvis_response_builder import JarvisResponseBuilder
from jarvis.jarvis_response_formatter import JarvisResponseFormatter
from jarvis.jarvis_validator import JarvisValidator
from reasoning import ReasoningManager, ReasoningRequest


class JarvisController:
    """Runs the architecture-only request pipeline."""

    def __init__(
        self,
        intent_engine: JarvisIntentEngine | None = None,
        decision_engine: JarvisDecisionEngine | None = None,
        planning: JarvisPlanning | None = None,
        dispatcher: JarvisDispatcher | None = None,
        response_builder: JarvisResponseBuilder | None = None,
        response_formatter: JarvisResponseFormatter | None = None,
        validator: JarvisValidator | None = None,
        reasoning_manager: ReasoningManager | None = None,
    ) -> None:
        self.intent_engine = intent_engine or JarvisIntentEngine()
        self.decision_engine = decision_engine or JarvisDecisionEngine()
        self.planning = planning or JarvisPlanning()
        self.dispatcher = dispatcher or JarvisDispatcher()
        self.response_builder = response_builder or JarvisResponseBuilder()
        self.response_formatter = response_formatter or JarvisResponseFormatter()
        self.validator = validator or JarvisValidator()
        self.reasoning_manager = reasoning_manager or ReasoningManager()
        if not self.reasoning_manager.initialized:
            self.reasoning_manager.initialize()
        self.initialized = True

    def handle(self, request: JarvisRequest, context: JarvisContext) -> JarvisResponse:
        """Handle a request through the executive pipeline."""
        validation = self.validator.validate_request(request)
        if not validation.valid:
            return JarvisResponse(
                request_id=request.request_id,
                content="JARVIS Executive could not process an empty request.",
                success=False,
                warnings=validation.errors,
            )
        reasoning = self.reasoning_manager.reason(
            ReasoningRequest(
                request_id=request.request_id,
                content=request.content,
                context={
                    "conversation_id": request.conversation_id,
                    "strategy_hint": request.strategy_hint.value if request.strategy_hint else None,
                    "metadata": dict(request.metadata),
                    "personal_context": request.metadata.get("personal_context", {}),
                    "resolved_context": request.metadata.get("resolved_context", {}),
                    "goal_analysis": request.metadata.get("goal_analysis", {}),
                },
            ),
            None,
        )
        context.metadata["reasoning"] = reasoning.metadata
        intent = self.intent_engine.identify(request)
        decision = self.decision_engine.decide(request.content, intent)
        context.execution_strategy = decision.strategy
        context.current_department = decision.department
        plan = self.planning.create_plan(decision)
        dispatch = self.dispatcher.dispatch(decision, plan)
        response = self.response_builder.build(request, decision, plan, dispatch)
        self.validator.validate_response(response)
        return response
