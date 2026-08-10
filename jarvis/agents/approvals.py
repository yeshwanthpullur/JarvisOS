"""Approval policy helpers for governed delegation decisions."""

from __future__ import annotations

from .models import AgentApprovalState, AgentExecutionMode, AgentRiskLevel


def requires_approval(risk_level: AgentRiskLevel, execution_mode: AgentExecutionMode, has_side_effects: bool = False) -> bool:
    if execution_mode in {AgentExecutionMode.PLAN_ONLY, AgentExecutionMode.DRY_RUN} and not has_side_effects:
        return False
    return has_side_effects or risk_level in {AgentRiskLevel.HIGH, AgentRiskLevel.CRITICAL}


def is_execution_allowed(
    risk_level: AgentRiskLevel,
    execution_mode: AgentExecutionMode,
    approval_state: AgentApprovalState,
    *,
    block_critical: bool = True,
) -> bool:
    if execution_mode in {AgentExecutionMode.PLAN_ONLY, AgentExecutionMode.DRY_RUN}:
        return True
    if block_critical and risk_level is AgentRiskLevel.CRITICAL:
        return False
    return approval_state is AgentApprovalState.GRANTED


def approval_summary(required: bool, state: AgentApprovalState) -> str:
    return f"approval_required={'yes' if required else 'no'} approval_state={state.value}"

