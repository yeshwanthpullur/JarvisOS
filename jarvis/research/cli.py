"""Bounded CLI rendering for research planning."""

from __future__ import annotations

from .agent import ResearchAgent
from .planner import classify_research_intent
from .safety import evaluate_research_safety


def render_research_command(agent: ResearchAgent, command: str, arguments: tuple[str, ...]) -> str:
    if command == "research status":
        status = agent.status()
        return "Research status: " + " ".join(f"{key}={str(value).lower() if isinstance(value, bool) else value}" for key, value in status.items())
    if command == "research help":
        return "Research commands: research status, help, plan, safety, sources, summarize, evidence <id>, show <id>, history."
    if command == "research history":
        entries = agent.history_records()[-10:]
        return "Research history: " + (", ".join(f"{item.request_id}:{item.intent}:{item.status}" for item in entries) or "none")
    query = " ".join(arguments).strip()
    if command == "research evidence":
        result = agent.show(arguments[0] if arguments else "")
        if result is None:
            return "Research result not found."
        evidence = ",".join(f"{item.evidence_id}:{item.source_type.value}:{item.confidence:.2f}" for item in result.evidence) or "none"
        return f"Research evidence: status={result.status.value} count={len(result.evidence)} refs={evidence}"
    if command == "research show":
        result = agent.show(arguments[0] if arguments else "")
        if result is None:
            return "Research result not found."
        intent = result.plan.research_type.value if result.plan else "unknown"
        return f"Research result: status={result.status.value} request_id={result.request_id} intent={intent} evidence={len(result.evidence)}"
    if not query:
        return f"Usage: {command} <query>"
    if command == "research safety":
        intent = classify_research_intent(query)
        decision = evaluate_research_safety(query, intent)
        return f"Research safety: intent={intent.value} risk={decision.risk_level.value} allowed={'yes' if decision.allowed else 'no'} restricted_domain={decision.restricted_domain or 'none'} confirmation_required={'yes' if decision.action_confirmation_required else 'no'}."
    if command == "research sources":
        plan = agent.plan(query)
        return f"Research sources: allowed={','.join(item.value for item in plan.allowed_sources) or 'none'} blocked={','.join(item.value for item in plan.blocked_sources) or 'none'} needs_web={'yes' if plan.needs_web else 'no'} needs_documents={'yes' if plan.needs_documents else 'no'} retrieved=0."
    if command == "research summarize":
        result = agent.summarize(query)
        summary = result.summary.answer if result.summary else "Evidence unavailable."
        return f"Research summary: status={result.status.value} {summary[:800]}"
    result = agent.plan_result(query, depth=agent.default_depth)
    plan = result.plan
    return f"Research plan: id={result.request_id} intent={plan.research_type.value} depth={plan.depth.value} status={plan.status.value} clarification={'yes' if plan.needs_user_clarification else 'no'} steps=" + " | ".join(plan.steps)
