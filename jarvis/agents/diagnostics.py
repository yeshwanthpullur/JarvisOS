"""Bounded public diagnostics for the agent registry."""

from __future__ import annotations

from .registry import AgentRegistry


def agent_diagnostics(registry: AgentRegistry) -> dict[str, object]:
    summary = registry.registry_summary()
    return {**summary, "validation_errors": registry.validate_registry()[:10]}


def render_agent_command(registry: AgentRegistry, command: str, arguments: tuple[str, ...] = ()) -> str:
    entries = registry.list_agents()
    if command in {"agents", "agent status"}:
        data = registry.registry_summary()
        return (
            "Agent system: status=ready mode=plan_only "
            f"agents={data['total_agents']} ready={data['ready_agents']} "
            f"unavailable={data['unavailable_agents']} capabilities={data['total_capabilities']}."
        )
    if command == "agent list":
        return "Agents: " + (", ".join(f"{item.name}:{item.status.value}" for item in entries[:25]) or "none")
    if command == "agent capabilities":
        values = registry.list_capabilities()[:40]
        return "Agent capabilities: " + (", ".join(f"{agent}.{name}:{kind}" for agent, name, kind in values) or "none")
    if command == "agent show":
        name = arguments[0] if arguments else ""
        entry = registry.get_agent(name)
        if entry is None:
            return "Agent not found."
        capabilities = ", ".join(cap.name for cap in entry.capabilities[:15]) or "none"
        return (
            f"Agent {entry.name}: status={entry.status.value} enabled={'yes' if entry.enabled else 'no'} "
            f"local_only={'yes' if entry.local_only else 'no'} capabilities={capabilities} reason={entry.reason[:240]}"
        )
    if command == "agent find":
        query = arguments[0] if arguments else ""
        matches = registry.find_by_capability(query, executable_only=False)
        return f"Agent matches for {query or 'none'}: " + (", ".join(item.name for item in matches[:20]) or "none")
    if command == "agent diagnostics":
        data = agent_diagnostics(registry)
        return "Agent diagnostics: " + ", ".join(f"{key}={value}" for key, value in data.items() if key != "validation_errors")
    if command in {"agent ready", "agent unavailable", "agent future"}:
        if command == "agent ready":
            selected = tuple(item for item in entries if item.status.value == "ready")
        elif command == "agent future":
            selected = tuple(item for item in entries if item.health == "future")
        else:
            selected = tuple(item for item in entries if item.status.value != "ready")
        return command.title() + ": " + (", ".join(f"{item.name}:{item.health}" for item in selected[:25]) or "none")
    if command == "agent risks":
        values = tuple((entry.name, cap.name, cap.risk_level.value) for entry in entries for cap in entry.capabilities if cap.risk_level.value in {"high", "critical"})
        return "Agent risks: " + (", ".join(f"{agent}.{capability}:{risk}" for agent, capability, risk in values[:30]) or "none")
    if command == "agent approvals":
        values = tuple((entry.name, cap.name) for entry in entries for cap in entry.capabilities if cap.requires_approval)
        return "Agent approvals: " + (", ".join(f"{agent}.{capability}" for agent, capability in values[:30]) or "none")
    return "Agent command unavailable."
