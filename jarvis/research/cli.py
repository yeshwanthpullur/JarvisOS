"""Bounded CLI rendering for research planning."""

from __future__ import annotations

from .agent import ResearchAgent
from .models import ResearchDepth
from .planner import classify_research_intent, classify_research_risk


def render_research_command(agent: ResearchAgent, command: str, arguments: tuple[str, ...]) -> str:
    if command == "research status":
        status = agent.status()
        return "Research status: " + " ".join(f"{key}={str(value).lower() if isinstance(value, bool) else value}" for key, value in status.items())
    if command == "research help":
        return "Research commands: research status, help, plan, safety, sources, summarize, evidence <id>, show <id>, history."
    if command == "research history":
        entries = agent.history[-10:]
        return "Research history: " + (", ".join(result.request_id for result in entries) or "none")
    query = " ".join(arguments).strip()
    if command == "research evidence":
        result = agent.show(arguments[0] if arguments else "")
        if result is None:
            return "Research result not found."
        summary = result.summary.answer if result.summary else "none"
        return f"Research evidence: status={result.status.value} summary={summary[:400]}"
    if command == "research show":
        result = agent.show(arguments[0] if arguments else "")
        if result is None:
            return "Research result not found."
        return f"Research result: status={result.status.value} request_id={result.request_id} evidence={len(result.evidence)}"
    if not query:
        return f"Usage: {command} <query>"
    if command == "research safety":
        intent = classify_research_intent(query)
        risk = classify_research_risk(query, intent)
        return f"Research safety: intent={intent.value} risk={risk.value} allowed={'no' if risk.value == 'blocked' else 'yes'}."
    if command == "research sources":
        plan = agent.plan(query)
        return f"Research sources: allowed={','.join(item.value for item in plan.allowed_sources) or 'none'} blocked={','.join(item.value for item in plan.blocked_sources) or 'none'} needs_web={'yes' if plan.needs_web else 'no'} needs_documents={'yes' if plan.needs_documents else 'no'}."
    if command == "research summarize":
        result = agent.summarize(query)
        summary = result.summary.answer if result.summary else "Evidence unavailable."
        return f"Research summary: status={result.status.value} {summary[:800]}"
    plan = agent.plan(query, depth=ResearchDepth.STANDARD)
    return "Research plan: " + " | ".join(plan.steps)
