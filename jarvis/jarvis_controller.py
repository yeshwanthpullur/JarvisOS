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
from provider_execution import ExecutionManager
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
        agent_manager = context.agent_manager or context.metadata.get("agent_manager")
        orchestrator = getattr(agent_manager, "orchestrator", None)
        if orchestrator is not None:
            session_metadata = dict(request.metadata.get("session_metadata", {}) or {})
            configured_mode = session_metadata.get("multiagent_mode")
            if configured_mode:
                try:
                    orchestrator.set_mode(str(configured_mode))
                except ValueError:
                    pass
            assessment = orchestrator.assess(
                request.content,
                {**dict(request.metadata), "request_id": request.request_id},
            )
            context.metadata["multiagent_assessment"] = assessment
            if assessment.requires_multi_agent:
                coordination = orchestrator.coordinate(
                    objective=request.content,
                    parent_request_id=request.request_id,
                    assessment=assessment,
                    metadata={
                        **dict(request.metadata),
                        "conversation_id": request.conversation_id,
                        "selected_context": request.metadata.get("resolved_context", {}),
                        "execution_policy": session_metadata.get("execution_policy", request.metadata.get("execution_policy", "automatic")),
                        "provider_preference": session_metadata.get("provider_preference", request.metadata.get("provider_preference")),
                        "model_preference": session_metadata.get("model_preference", request.metadata.get("model_preference")),
                        "local_only": bool(session_metadata.get("local_only", request.metadata.get("local_only", False))),
                        "cloud_only": bool(session_metadata.get("cloud_only", request.metadata.get("cloud_only", False))),
                    },
                    executive_approved=True,
                )
                if coordination.synthesis:
                    return JarvisResponse(
                        request_id=request.request_id,
                        content=coordination.synthesis,
                        response_type="multiagent",
                        execution_summary={
                            "coordination_id": coordination.coordination_id,
                            "collaboration_mode": coordination.mode.value,
                            "coordination_status": coordination.status.value,
                            "participating_agents": coordination.plan.participating_agents,
                            "subtask_ids": tuple(item.subtask_id for item in coordination.plan.subtasks),
                            "completed_results": sum(item.success for item in coordination.results),
                            "conflicts": len(coordination.conflicts),
                        },
                        warnings=coordination.warnings,
                        streaming_metadata={
                            "coordination_id": coordination.coordination_id,
                            "parent_request_id": coordination.parent_request_id,
                            "collaboration_mode": coordination.mode.value,
                            "agent_results": tuple(
                                {
                                    "agent_id": item.agent_id,
                                    "subtask_id": item.subtask_id,
                                    "status": item.status.value,
                                    "provider_id": item.provider_metadata.get("provider_id"),
                                    "model_id": item.provider_metadata.get("model_id"),
                                }
                                for item in coordination.results
                            ),
                        },
                    )
        provider_execution_manager = context.metadata.get("provider_execution_manager")
        if decision.strategy.value == "direct" and provider_execution_manager is not None and isinstance(provider_execution_manager, ExecutionManager):
            session_metadata = dict(request.metadata.get("session_metadata", {}) or {})
            execution_policy = session_metadata.get("execution_policy", request.metadata.get("execution_policy", "automatic"))
            provider_preference = session_metadata.get("provider_preference", request.metadata.get("provider_preference"))
            model_preference = session_metadata.get("model_preference", request.metadata.get("model_preference"))
            local_only = bool(session_metadata.get("local_only", request.metadata.get("local_only", False)))
            cloud_only = bool(session_metadata.get("cloud_only", request.metadata.get("cloud_only", False)))
            provider_request = provider_execution_manager.build_execution_request(
                intent=decision.goal,
                goal=decision.goal,
                request_id=request.request_id,
                conversation_id=request.conversation_id,
                priority=request.priority,
                provider=provider_preference,
                model=model_preference,
                context=dict(request.metadata.get("resolved_context", {})),
                metadata={
                    **dict(request.metadata),
                    "system_instructions": request.metadata.get("system_instructions", ""),
                    "selected_context": request.metadata.get("resolved_context", {}),
                    "retrieved_evidence": tuple(request.metadata.get("retrieved_evidence", ()) or ()),
                    "local_only": local_only,
                    "cloud_only": cloud_only,
                    "execution_policy": execution_policy,
                    "streaming": bool(request.metadata.get("streaming", False)),
                    "temperature": request.metadata.get("temperature"),
                    "max_output_tokens": request.metadata.get("max_output_tokens"),
                    "stop_conditions": tuple(request.metadata.get("stop_conditions", ()) or ()),
                    "timeout_seconds": request.metadata.get("timeout_seconds"),
                    "response_schema": request.metadata.get("response_schema"),
                    "task_type": request.metadata.get("task_type"),
                    "required_capabilities": request.metadata.get("required_capabilities", ()),
                    "provider_preference": provider_preference,
                    "model_preference": model_preference,
                },
            )
            provider_result = provider_execution_manager.execute_through_provider_router(provider_request)
            response = JarvisResponse(
                request_id=request.request_id,
                content=provider_result.response,
                response_type=decision.strategy.value,
                execution_summary={
                    "goal": decision.goal,
                    "strategy": decision.strategy.value,
                    "department": dispatch.selected_department,
                    "plan_steps": len(plan.steps),
                    "context_applied": bool(request.metadata.get("resolved_context")),
                    "context_status": request.metadata.get("resolved_context", {}).get("status"),
                    "active_objective": request.metadata.get("resolved_context", {}).get("active_objective"),
                    "continuation_next_step": request.metadata.get("resolved_context", {}).get("next_step"),
                    "context_ambiguity": request.metadata.get("resolved_context", {}).get("ambiguity", False),
                    "goal_context_applied": bool(request.metadata.get("goal_analysis")),
                    "goal_analysis_type": request.metadata.get("goal_analysis", {}).get("analysis_type"),
                    "goal_summary": request.metadata.get("goal_analysis", {}).get("summary"),
                    "personal_context_applied": bool(request.metadata.get("personal_context"))
                    and not bool(request.metadata.get("personal_context", {}).get("override_current_instruction")),
                    "personal_preferences": len(request.metadata.get("personal_context", {}).get("active_preferences", ())),
                    "provider_id": provider_result.provider,
                    "model_id": provider_result.model,
                    "latency_ms": provider_result.latency_ms,
                    "estimated_cost": provider_result.estimated_cost,
                    "provider_execution": provider_result.statistics,
                },
                diagnostics=tuple(
                    str(item) for item in (
                        provider_result.warnings
                        + tuple(provider_result.diagnostics.keys())
                    )
                ),
                warnings=provider_result.warnings,
                streaming_metadata={
                    "provider_id": provider_result.provider,
                    "model_id": provider_result.model,
                    "latency_ms": provider_result.latency_ms,
                    "estimated_cost": provider_result.estimated_cost,
                    "provider_execution_success": provider_result.success,
                    "provider_execution_diagnostics": provider_result.diagnostics,
                },
            )
            return response
        response = self.response_builder.build(request, decision, plan, dispatch)
        self.validator.validate_response(response)
        return response
