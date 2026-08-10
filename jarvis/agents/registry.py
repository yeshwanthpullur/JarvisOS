"""Deterministic registry for governed JARVIS agent metadata."""

from __future__ import annotations

from .models import AgentCapabilityType, AgentRegistryEntry, AgentStatus


class AgentRegistryError(ValueError):
    """Raised when registry invariants are violated."""


class AgentRegistry:
    def __init__(self, entries: tuple[AgentRegistryEntry, ...] = (), max_agents: int = 64) -> None:
        self.max_agents = max(1, min(int(max_agents), 128))
        self._entries: dict[str, AgentRegistryEntry] = {}
        for entry in entries:
            self.register_agent(entry)

    def register_agent(self, entry: AgentRegistryEntry) -> None:
        if entry.name in self._entries:
            raise AgentRegistryError(f"duplicate_agent:{entry.name}")
        if len(self._entries) >= self.max_agents:
            raise AgentRegistryError("agent_registry_limit_exceeded")
        self._entries[entry.name] = entry

    def unregister_agent(self, name: str) -> bool:
        return self._entries.pop(name, None) is not None

    def get_agent(self, name: str) -> AgentRegistryEntry | None:
        return self._entries.get(name)

    def list_agents(self, *, executable_only: bool = False) -> tuple[AgentRegistryEntry, ...]:
        entries = tuple(self._entries.values())
        if executable_only:
            entries = tuple(item for item in entries if item.enabled and item.status is AgentStatus.READY)
        return entries

    def list_capabilities(self) -> tuple[tuple[str, str, str], ...]:
        return tuple(
            (entry.name, capability.name, capability.capability_type.value)
            for entry in self._entries.values()
            for capability in entry.capabilities
        )

    def find_by_capability(self, query: str | AgentCapabilityType, *, executable_only: bool = True) -> tuple[AgentRegistryEntry, ...]:
        needle = query.value if isinstance(query, AgentCapabilityType) else str(query).strip().lower()
        matches = []
        for entry in self._entries.values():
            if executable_only and (not entry.enabled or entry.status is not AgentStatus.READY):
                continue
            if any(cap.name.lower() == needle or cap.capability_type.value == needle for cap in entry.capabilities):
                matches.append(entry)
        return tuple(matches)

    def agent_status(self, name: str) -> AgentStatus | None:
        entry = self.get_agent(name)
        return entry.status if entry else None

    def registry_summary(self) -> dict[str, int | bool]:
        entries = self.list_agents()
        capabilities = [cap for entry in entries for cap in entry.capabilities]
        return {
            "total_agents": len(entries),
            "ready_agents": sum(item.status is AgentStatus.READY for item in entries),
            "unavailable_agents": sum(item.status in {AgentStatus.UNAVAILABLE, AgentStatus.NOT_CONFIGURED, AgentStatus.ERROR} for item in entries),
            "disabled_agents": sum(item.status is AgentStatus.DISABLED for item in entries),
            "total_capabilities": len(capabilities),
            "high_risk_capabilities": sum(cap.risk_level.value in {"high", "critical"} for cap in capabilities),
            "approval_required_capabilities": sum(cap.requires_approval for cap in capabilities),
            "local_only_capabilities": sum(cap.local_only for cap in capabilities),
            "valid": not self.validate_registry(),
        }

    def validate_registry(self) -> tuple[str, ...]:
        errors: list[str] = []
        if len(self._entries) > self.max_agents:
            errors.append("agent_registry_limit_exceeded")
        for entry in self._entries.values():
            names = [cap.name for cap in entry.capabilities]
            if len(names) != len(set(names)):
                errors.append(f"duplicate_capability:{entry.name}")
            if entry.status is AgentStatus.READY and not entry.enabled:
                errors.append(f"ready_disabled:{entry.name}")
        return tuple(errors[:32])

