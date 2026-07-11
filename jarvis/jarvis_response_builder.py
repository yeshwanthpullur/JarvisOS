"""Response builder for Executive JARVIS."""

from __future__ import annotations

from jarvis.jarvis_decision_engine import JarvisDecision
from jarvis.jarvis_dispatcher import DispatchResult
from jarvis.jarvis_planning import JarvisExecutionPlan
from jarvis.jarvis_request import JarvisRequest
from jarvis.jarvis_response import JarvisResponse


class JarvisResponseBuilder:
    """Builds unified responses from pipeline metadata."""

    initialized = True

    def build(
        self,
        request: JarvisRequest,
        decision: JarvisDecision,
        plan: JarvisExecutionPlan,
        dispatch: DispatchResult,
    ) -> JarvisResponse:
        """Build a response without invoking providers."""
        content = "JARVIS Executive received the request and prepared an architecture-only execution plan."
        return JarvisResponse(
            request_id=request.request_id,
            content=content,
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
            },
        )
